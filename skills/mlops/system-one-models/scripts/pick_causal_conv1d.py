#!/usr/bin/env python3
"""Pick + install the causal-conv1d prebuilt wheel that matches THIS venv exactly.

Why: PyPI ships only an sdist, and compiling it needs the CUDA toolkit (nvcc). A WSL2 host that
merely passes /dev/dxg through has the driver libs but no nvcc, so the build fails. Upstream
publishes cp310-cp313 / cu11-cu13 / torch2.6-2.10 / cxx11abiTRUE|FALSE wheels on GitHub releases.

Usage: pick_causal_conv1d.py [--dry-run]
"""
import json, os, subprocess, sys, urllib.request

import torch

REPO = "Dao-AILab/causal-conv1d"
URL = "https://api.github.com/repos/%s/releases" % REPO


def fetch_releases():
    """Authenticated gh first (anonymous GitHub API is only 60 req/h and does rate-limit)."""
    try:
        out = subprocess.check_output(["gh", "api", "repos/%s/releases" % REPO, "--paginate"],
                                      text=True, stderr=subprocess.DEVNULL).strip()
        dec, idx, rels = json.JSONDecoder(), 0, []
        while idx < len(out):
            obj, end = dec.raw_decode(out, idx)
            rels.extend(obj if isinstance(obj, list) else [obj])
            idx = end
            while idx < len(out) and out[idx] in " \n\r\t":
                idx += 1
        if rels:
            print("release list: gh (%d releases)" % len(rels), flush=True)
            return rels
    except Exception as exc:
        print("gh unavailable (%s); falling back to anonymous GitHub API" % type(exc).__name__,
              flush=True)
    req = urllib.request.Request(URL, headers={"User-Agent": "system-one-models"})
    if os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", "Bearer " + os.environ["GITHUB_TOKEN"])
    with urllib.request.urlopen(req, timeout=60) as fh:
        return json.load(fh)


abi = "TRUE" if torch._C._GLIBCXX_USE_CXX11_ABI else "FALSE"
tmaj, tmin = torch.__version__.split("+")[0].split(".")[:2]
cuda = (torch.version.cuda or "").replace(".", "")           # "12.8" -> "128"
cutag = "cu" + cuda[:2]                                       # -> "cu12"
cp = "cp%d%d" % sys.version_info[:2]
plat = "linux_x86_64" if sys.platform == "linux" and sys.maxsize > 2**32 else "linux_aarch64"

want = ("torch" + ".".join([tmaj, tmin]), cutag, "cxx11abi" + abi, cp + "-" + cp, plat)
print("looking for:", want, flush=True)

for rel in fetch_releases():                                  # newest release first
    for asset in rel.get("assets", []):
        n = asset["name"]
        if n.endswith(".whl") and all(w in n for w in want):
            print("MATCH", n, flush=True)
            if "--dry-run" in sys.argv:
                print("DRY_RUN_OK", asset["browser_download_url"], flush=True)
                sys.exit(0)
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-deps", "-U",
                                   "--force-reinstall", asset["browser_download_url"]])
            print("INSTALLED", n, flush=True)
            sys.exit(0)

print("NO MATCHING WHEEL for", want, flush=True)
print("-> install the CUDA toolkit so it can build from source, or the conv1d fast path stays "
      "on the torch fallback", flush=True)
sys.exit(1)
