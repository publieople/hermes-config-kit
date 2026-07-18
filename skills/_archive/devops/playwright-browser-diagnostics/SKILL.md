---
name: playwright-browser-diagnostics
description: Install and diagnose Playwright-based packages (Playwright, CloakBrowser, etc.) on Linux/WSL — handles externally-managed Python, system deps, proxy-based binary downloads, and runtime troubleshooting
tags:
  - devops
  - browser
  - playwright
  - chromium
  - wsl
  - troubleshooting
  - shared-libraries
triggers:
  - Installing Playwright-based packages (cloakbrowser, playwright, etc.) on Arch Linux / WSL
  - pip install fails with "externally managed environment" on Arch
  - First-run binary download (Chromium) times out in China — needs proxy setup
  - browser_navigate fails with Chrome exited early or missing shared library errors
  - Browser tool reports missing shared library like libnspr4.so
  - Playwright chromium crashes on startup with library not found
  - After WSL migration or Arch updates where browser stops working
  - Browser tool is broken on Linux
  - ldd output shows not found entries for Playwright chromium
---

# Playwright Browser Dependency Diagnostics

## Overview

Hermes Agent's built-in `browser` tool uses a Playwright-bundled Chromium binary. On Linux (especially Arch Linux in WSL), this binary can fail to launch if the system is missing required shared libraries. The error manifests as:

```
Chrome exited early (exit code: 127)
error while loading shared libraries: libnspr4.so: cannot open shared object file
```

This skill covers: detection, dependency installation, and verification.

## Installation (Playwright-based packages on WSL Arch)

When installing `playwright`-based packages (like `cloakbrowser`, `playwright` itself) on WSL Arch Linux, the system Python is **externally managed** — `pip install` fails with "externally managed environment".

### Step 0: Create a dedicated venv

```bash
uv venv ~/venvs/<name>           # e.g., ~/venvs/cloak
source ~/venvs/<name>/bin/activate
uv pip install <package>          # e.g., cloakbrowser
```

This installs `playwright` as a dependency (e.g., `playwright==1.59.0` for `cloakbrowser==0.3.28`).

### Step 1: First-run binary download (proxy needed in China)

On first import/launch, the package auto-downloads its Chromium binary (~200MB) to `~/.cache/<package>/`. Without proxy this times out in China:

```bash
# Ensure proxy is set before first launch
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
source ~/venvs/<name>/bin/activate
python3 -c "from cloakbrowser import launch; b = launch(headless=True); print('OK'); b.close()"
```

**Binary locations:**
- Playwright: `~/.cache/ms-playwright/`
- CloakBrowser: `~/.cache/cloakbrowser/` (custom Chromium with C++ fingerprint patches)

### Step 2: Verify the full import + launch

```bash
source ~/venvs/<name>/bin/activate
python3 -c "
from cloakbrowser import launch
b = launch(headless=True)
print('Browser launched OK, version:', b.version if hasattr(b, 'version') else 'launched')
b.close()
"
```

## Detection

### Step 1: Find the Chromium binary

Playwright stores browser binaries under `~/.cache/ms-playwright/`. CloakBrowser stores its custom Chromium under `~/.cache/cloakbrowser/`:

```bash
ls ~/.cache/ms-playwright/chromium-*/chrome-linux64/chrome
ls ~/.cache/cloakbrowser/*/chrome-linux64/chrome 2>/dev/null
```

### Step 2: Check which libraries are missing

```bash
ldd ~/.cache/ms-playwright/chromium-*/chrome-linux64/chrome 2>&1 | grep "not found"
```

If this returns empty (no output, exit code 1 from grep), all shared library dependencies are satisfied.

### Step 3: Check browser_navigate in Hermes

Run a quick smoke test:

```python
browser_navigate(url="https://example.com")
```

If it returns `success: true` with a page title and snapshot, the browser is working.

## Fix: Install Missing System Libraries

### Arch Linux (including WSL2 Arch)

Install the packages that contain the common missing libraries:

```bash
sudo pacman -S --needed nspr nss atk at-spi2-atk cups libxkbcommon libxcomposite libxdamage libxrandr at-spi2-core
```

| Package | Provides |
|---------|----------|
| `nspr` | `libnspr4.so` |
| `nss` | `libnss3.so`, `libnssutil3.so`, `libsmime3.so` |
| `atk` | `libatk-1.0.so.0` |
| `at-spi2-atk` | `libatk-bridge-2.0.so.0` |
| `at-spi2-core` | `libatspi.so.0` |
| `cups` | `libcups.so.2` |
| `libxkbcommon` | `libxkbcommon.so.0` |
| `libxcomposite` | `libXcomposite.so.1` |
| `libxdamage` | `libXdamage.so.1` |
| `libxrandr` | `libXrandr.so.2` |

### Ubuntu / Debian

```bash
sudo apt install -y libnspr4 libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libatspi2.0-0
```

Or use Playwright's own dependency installer:

```bash
npx playwright install-deps chromium
```

### macOS

Not applicable. Playwright's macOS build bundles all dependencies statically.

### WSL-Specific Notes

- WSL2 Arch does not ship with X11/GTK libraries by default — the packages above are the minimum set.
- For full desktop-like rendering, also install `gtk3`, `gdk-pixbuf2`, `libnotify`, `libxss`, `libxtst`.
- After installing, the browser works in headless mode even without an X server.

## Verification

### Quick test via Hermes tool

```python
# Should return success: true with page content
browser_navigate(url="https://example.com")

# Verify snapshot works
browser_snapshot()

# Verify interaction works
browser_click(ref="e2")
```

### Direct Chromium test (optional)

If Hermes tools are unavailable, test the binary directly:

```python
import subprocess
import os, json

chrome_path = os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-linux64/chrome")
# Use glob to find actual path, then:
result = subprocess.run(
    [chrome_path, "--headless", "--no-sandbox", "--disable-gpu", "--dump-dom", "https://example.com"],
    capture_output=True, text=True, timeout=15
)
print("exit:", result.returncode, "| stdout:", result.stdout[:200] if result.stdout else "empty", "| stderr:", result.stderr[:200] if result.stderr else "none")
```

## Pitfalls

- Do NOT use `cat`/`head`/`tail` to read files — blocked by Hermes security. Use `read_file()` instead.
- Do NOT use `sed` for edits — blocked. Use `patch()` instead.
- Do NOT use `ls` to list directories — blocked for some scan configs. Use `search_files(target='files', ...)` instead.
- The browser process can get stuck — after a failed navigation, stale Chromium processes may block future attempts. Clean up: `pkill -f "ms-playwright"` then try again.
- example.com works but real sites timeout — this is usually a WSL network issue (DNS, firewall, or China Great Firewall), not a browser dependency problem. Test with httpbin.org or domestic sites to confirm.
- Arch Linux on WSL — sudo requires a password. Politely ask the user to run the pacman command.
- ldd returning not found for crypto/libssl — those are typically statically linked in Playwright's Chromium, not a real dependency issue.

## Post-Fix: Proxy Setup for GFW-Blocked Sites (WSL in China)

After fixing Playwright dependencies, the next bottleneck is typically that the browser can reach domestic sites but times out on international ones. The fix is to route Chromium through a proxy (Clash/V2ray/etc.) running on the Windows host.

### WSL-Reachability

Clash running on Windows at 127.0.0.1:7890 is reachable from WSL2 — test with:
```bash
curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://127.0.0.1:7890
# Returns 400 if reachable
```

### 1. Hermes env_passthrough

Add these to `~/.hermes/config.yaml` under `terminal:` so Hermes forwards proxy env vars to all child processes including Chromium:
```yaml
env_passthrough:
- http_proxy
- https_proxy
- ALL_PROXY
```

This tells Hermes: if these env vars are set in **Hermes' own process environment**, pass them through to subprocesses (including the browser's Chromium).

### 2. Shell config (fish example)

To have proxy vars always set when opening a terminal:
```fish
# In ~/.config/fish/config.fish
set -x http_proxy "http://127.0.0.1:7890"
set -x https_proxy "http://127.0.0.1:7890"
set -x ALL_PROXY "socks5://127.0.0.1:7890"
```

For bash/zsh, use `export` instead.

### Important Caveat

- The proxy must be **running on Windows** before Hermes starts, or network will break entirely.
- If Clash is off, clear vars: `set -e http_proxy https_proxy ALL_PROXY` (fish) or `unset http_proxy https_proxy ALL_PROXY` (bash).
- env_passthrough only works if the vars are in the **Hermes process** environment — if Hermes is launched as a systemd service or from a session that doesn't source the shell config, they won't be present. Launch Hermes from the terminal where proxy is set.
