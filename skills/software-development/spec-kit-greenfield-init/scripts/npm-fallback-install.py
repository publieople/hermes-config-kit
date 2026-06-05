#!/usr/bin/env python3
"""npm-fallback-install.py — Manual npm package installer.

When `npm install` exits 0 but creates no node_modules/ (npm 11+ bug on Node 26),
use this script as a fallback. It downloads via `npm pack` and extracts tarballs
directly into node_modules/, including transitive dependencies and Vite 8 native bindings.

Usage:
    python3 scripts/npm-fallback-install.py           # uses cwd
    python3 scripts/npm-fallback-install.py --dir frontend  # explicit dir
"""

import json
import os
import shutil
import subprocess
import sys
import tarfile
from collections import deque
from pathlib import Path


def npm_pack(name: str, workdir: str) -> str | None:
    """Download a package tarball via npm pack. Returns the .tgz filename."""
    result = subprocess.run(
        ["npm", "pack", name],
        capture_output=True, text=True, timeout=60,
        cwd=workdir,
    )
    lines = result.stdout.strip().split("\n")
    tgz = lines[-1].strip() if lines else ""
    if result.returncode != 0 or not tgz.endswith(".tgz"):
        print(f"  SKIP {name}: {result.stderr.strip() or 'no tarball'}")
        return None
    return tgz


def extract_tarball(tgz_path: str, dest: str):
    """Extract an npm pack tarball (has 'package/' prefix) to dest."""
    os.makedirs(dest, exist_ok=True)
    with tarfile.open(tgz_path) as tar:
        for member in tar.getmembers():
            if member.name.startswith("package/"):
                member.name = member.name[8:]
                if member.name:
                    tar.extract(member, dest)


def get_deps(name: str, nm: str) -> dict:
    """Get dependencies from an installed package's package.json."""
    pkg_path = os.path.join(nm, name, "package.json")
    if not os.path.exists(pkg_path):
        return {}
    with open(pkg_path) as f:
        return json.load(f).get("dependencies", {})


# Known native bindings needed by Vite 8 / rolldown / lightningcss
# Add more as needed for different platforms
NATIVE_BINDINGS = [
    "@rolldown/binding-linux-x64-gnu",
    "@rolldown/binding-linux-x64-musl",
    "lightningcss-linux-x64-gnu",
    "lightningcss-linux-x64-musl",
    "@oxc-project/types",
]


def install_native_bindings(nm: str, tmp_dir: str):
    """Install Vite 8 native bindings (listed as optionalDependencies)."""
    print("\n-- Installing native bindings for Vite 8 --")
    for name in NATIVE_BINDINGS:
        parts = name.split("/")
        dest = os.path.join(nm, *parts) if len(parts) > 1 else os.path.join(nm, name)
        if os.path.exists(os.path.join(dest, "package.json")):
            print(f"  OK {name} (already installed)")
            continue
        tgz = npm_pack(name, tmp_dir)
        if tgz:
            os.makedirs(dest, exist_ok=True)
            extract_tarball(os.path.join(tmp_dir, tgz), dest)
            os.unlink(os.path.join(tmp_dir, tgz))
            print(f"  INSTALLED {name}")


def main():
    # Parse --dir argument
    frontend_dir = Path.cwd()
    if len(sys.argv) > 2 and sys.argv[1] == "--dir":
        frontend_dir = Path(sys.argv[2]).resolve()
    elif len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    pkg_json = frontend_dir / "package.json"
    if not pkg_json.exists():
        print(f"ERROR: no package.json in {frontend_dir}")
        sys.exit(1)

    with open(pkg_json) as f:
        pkg = json.load(f)

    # Collect all deps (dependencies + devDependencies)
    all_deps = {}
    for src in [pkg.get("dependencies", {}), pkg.get("devDependencies", {})]:
        all_deps.update(src)

    if not all_deps:
        print("No dependencies in package.json")
        sys.exit(0)

    nm = frontend_dir / "node_modules"
    nm.mkdir(parents=True, exist_ok=True)
    tmp_dir = frontend_dir / ".npm-tmp"
    tmp_dir.mkdir(exist_ok=True)

    print(f"Installing {len(all_deps)} direct + transitive deps...")
    print(f"  Target: {nm}")

    installed = {}
    queue = deque(all_deps.keys())
    total = 0

    while queue:
        name = queue.popleft()
        safe_path = name.replace("/", os.sep)
        dest = nm / safe_path
        if name in installed or dest.exists():
            continue

        tgz = npm_pack(name, str(tmp_dir))
        if not tgz:
            continue

        try:
            extract_tarball(str(tmp_dir / tgz), str(dest))
        except Exception as e:
            print(f"  EXTRACT FAIL {name}: {e}")
            continue

        total += 1
        installed[name] = True
        print(f"  [{total}] {name}")

        # Queue transitive dependencies
        for subname in get_deps(name, str(nm)):
            if subname not in installed:
                queue.append(subname)

        # Clean up tarball
        (tmp_dir / tgz).unlink(missing_ok=True)

    # Cleanup temp dir
    shutil.rmtree(str(tmp_dir), ignore_errors=True)

    print(f"\nInstalled {total} packages into node_modules/")

    # Post-install: Vite 8 native bindings
    install_native_bindings(str(nm), str(frontend_dir / ".npm-tmp"))
    shutil.rmtree(str(frontend_dir / ".npm-tmp"), ignore_errors=True)

    listed = sorted(os.listdir(str(nm)))
    print(f"Total packages in node_modules/: {len(listed)}")


if __name__ == "__main__":
    main()
