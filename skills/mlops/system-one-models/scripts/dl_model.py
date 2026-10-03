#!/usr/bin/env python3
"""snapshot_download into a REAL directory (not the HF cache).

The HF cache stores repo files as symlinks; inference.py resolves paths relative to its own
file, so running out of the cache breaks checkpoint discovery. Always use local_dir + real name.
"""
import os, sys, time
os.environ["HF_HUB_DISABLE_XET"] = "1"   # xet on this host 401s
# NOTE: deliberately do NOT set HF_ENDPOINT. hf-mirror.com 308-redirects to huggingface.co and
# huggingface_hub then raises FileMetadataError("Distant resource does not seem to be on
# huggingface.co"). Direct huggingface.co works. Only set HF_ENDPOINT if the mirror works for you.
from huggingface_hub import snapshot_download

repo, local = sys.argv[1], sys.argv[2]
t0 = time.time()
p = snapshot_download(repo_id=repo, local_dir=local, max_workers=8)
print("DONE %s -> %s in %.1fs" % (repo, p, time.time() - t0), flush=True)
