# HyperFrames Setup on WSL + China Network

## First-Time Setup Checklist

### 1. Prerequisites
```bash
# Arch Linux
sudo pacman -S which        # HyperFrames uses `which` to find ffmpeg
sudo pacman -S ffmpeg       # if not already installed

# Verify
which ffmpeg       # must return a path
node --version     # must be >= 22
```

### 2. Install HyperFrames
```bash
npm install --ignore-scripts hyperframes@0.6.60
# --ignore-scripts avoids onnxruntime-node download failure
/bin/hyperframes in node_modules/.bin/
```

### 3. Chrome Headless Shell (manual download)

Puppeteer's built-in downloader corrupts files through proxy. Use curl directly:

```bash
# Set proxy (FlClash on Windows, port 7890)
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890

# Download
curl -L -o /tmp/chrome-headless-shell.zip \
  "https://storage.googleapis.com/chrome-for-testing-public/131.0.6778.85/linux64/chrome-headless-shell-linux64.zip"

# Extract to HyperFrames cache
unzip /tmp/chrome-headless-shell.zip -d /tmp/chrome-extracted/

# Create cache directory structure
mkdir -p /home/po/.cache/hyperframes/chrome/chrome-headless-shell/linux-131.0.6778.85/chrome-headless-shell-linux64/

# Copy binary
cp /tmp/chrome-extracted/chrome-headless-shell-linux64/chrome-headless-shell \
  /home/po/.cache/hyperframes/chrome/chrome-headless-shell/linux-131.0.6778.85/chrome-headless-shell-linux64/

# Copy REQUIRED resource files (missing these = "Invalid file descriptor to ICU data" error)
cp /tmp/chrome-extracted/chrome-headless-shell-linux64/icudtl.dat \
  /home/po/.cache/hyperframes/chrome/chrome-headless-shell/linux-131.0.6778.85/chrome-headless-shell-linux64/
cp /tmp/chrome-extracted/chrome-headless-shell-linux64/v8_context_snapshot.bin \
  /home/po/.cache/hyperframes/chrome/chrome-headless-shell/linux-131.0.6778.85/chrome-headless-shell-linux64/
cp -r /tmp/chrome-extracted/chrome-headless-shell-linux64/locales \
  /home/po/.cache/hyperframes/chrome/chrome-headless-shell/linux-131.0.6778.85/chrome-headless-shell-linux64/

chmod +x /home/po/.cache/hyperframes/chrome/chrome-headless-shell/linux-131.0.6778.85/chrome-headless-shell-linux64/chrome-headless-shell

# Verify
/tmp/node_modules/.bin/hyperframes doctor
# Should show: ✓ Chrome cache: ...chrome-headless-shell
```

### 4. Bundle GSAP Locally

CDN (cdn.jsdelivr.net, cdnjs.cloudflare.com, unpkg.com) is blocked in China:

```bash
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890

curl -sL -o gsap.min.js "https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"
```

Reference as `<script src="gsap.min.js"></script>` in index.html — never use CDN URLs.

### 5. Clash Proxy (FlClash)

- Windows process: `FlClashCore` (PID discovered via `powershell "Get-Process"`)
- Port: `127.0.0.1:7890` (HTTP)
- Access from WSL: `HTTP_PROXY=http://127.0.0.1:7890 HTTPS_PROXY=http://127.0.0.1:7890`
- Download speed through proxy: ~23 MB/s for Google CDN

## Common Render Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Browser was not found at ... executablePath` | Binary doesn't exist in cache or was corrupted | Manually download + copy (step 3) |
| `Invalid file descriptor to ICU data received` | Chrome's `icudtl.dat` missing from cache dir | Copy icudtl.dat alongside binary |
| `HeadlessExperimental.beginFrame unavailable` | Missing resource files or Chrome version mismatch | Ensure all resource files are in cache dir |
| CDN script timeout | GFW / network | Bundle all scripts locally |
| Snapshot shows content, MP4 is blank | Standard quality bitrate too low for text | `--quality high` |
| Auto worker calibration failed + long render | Chrome ran out of memory with 6 workers | `--workers 3` |

## Project Structure

```
my-video/
├── index.html          # Main composition (root timeline)
├── gsap.min.js         # Local GSAP (not CDN)
├── compositions/       # Sub-compositions (optional)
├── assets/             # Media files (optional)
├── snapshots/          # PNG screenshots (generated)
├── renders/            # Rendered MP4s (generated)
├── meta.json           # Project metadata
└── package.json
```

## First Render Walkthrough

```bash
cd /tmp
hyperframes init my-demo --non-interactive --example blank
cd my-demo
# Copy local gsap.min.js here
cp /path/to/gsap.min.js .

# Edit index.html with your composition
# Then:
hyperframes lint
hyperframes render --output demo.mp4 --quality high --workers 3
```

Expected: 3-6 second video renders in 5-10 seconds real time. 10+ second videos may need `--docker` or longer timeout.
