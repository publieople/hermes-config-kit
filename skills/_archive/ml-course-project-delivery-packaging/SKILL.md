---
name: ml-course-project-delivery-packaging
description: "Package a finished full-stack ML course project (Flask + Vue + PyTorch model) into a zero-config, single-click-runnable deliverable for teacher grading. Covers: pre-building Vue frontend, modifying Flask to serve static frontend, generating frozen requirements.txt, creating platform launcher scripts, and zipping for delivery."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [course-project, delivery, packaging, flask, vue, ml, grading]
    related_skills: [ml-web-course-project-wsl]
---

# ML Course Project Delivery Packaging

## Overview

After building a full-stack ML web app (Flask API + Vue frontend + PyTorch model weights) as a course project, you need to make it **double-click-runnable** for a teacher who is NOT a developer. The teacher likely:

- Has Python installed (or can install it)
- Does NOT have Node.js
- Should NOT need to run two terminals
- Should NOT need to configure anything
- Just wants to unzip, run, and see the demo

This skill wraps the entire project into a single-port, self-contained package.

## When to Use

**Trigger conditions — load this skill when ALL are true:**

- User has a finished Flask + Vue (or similar frontend framework) ML web app
- User says "pack this up for the teacher" or "make this runnable for grading"
- The project has: Python backend, npm-based frontend, and model weights/dependencies
- The deliverable needs to run on Windows (teacher's likely platform)

**Also trigger when:**
- User says "打包" (package) in context of a course project
- User wants a "one-click run" solution for non-technical users
- User has a dev setup with separate frontend/backend dev servers and needs to merge them

## Step-by-Step

### Step 1: Assess the Project

Identify:
- **Backend**: Flask app with API endpoints
- **Frontend**: Vue/React app with npm/package.json
- **Model**: Trained model weights (safetensors, bin, etc.)
- **How frontend calls API**: Relative paths (`/api/...`) or absolute URLs? If absolute, you may need to add a Vite proxy in dev and let Flask serve in production.
- **Entry point**: `backend/app.py` with `app.run()`

### Step 2: Build the Frontend (Production)

```bash
# Build in WSL ~/ to avoid /mnt/ EPERM issues
cp -r /mnt/e/.../frontend ~/tmp-fe-build/
cd ~/tmp-fe-build && npm install && npm run build
# Output goes to ~/tmp-fe-build/dist/
```

The `dist/` folder contains `index.html` + `assets/` (JS, CSS, images).

### Step 3: Create Submission Directory

Create a clean directory, exclude dev artifacts (`.venv`, `.git`, `node_modules`, `__pycache__`, `.spec`, `.github`, `.vscode`, course chapters unrelated to the project).

```
sentiment-analysis-submission/
├── backend/
│   ├── app.py              ← MODIFIED: serve frontend-dist
│   ├── config.py
│   ├── predictor.py        ← (project-specific files)
│   └── frontend-dist/      ← COPY of dist/ from Step 2
│       ├── index.html
│       └── assets/
├── model/
│   ├── inference.py
│   ├── config.py
│   └── saved_model/        ← Trained weights
├── requirements.txt         ← Generated (see Step 5)
├── run.bat                  ← Windows launcher
├── run.sh                   ← Linux/macOS launcher
└── README.md               ← Delivery-focused (see Step 7)
```

### Step 4: Modify Flask to Serve Static Frontend

In `backend/app.py`, add two routes AFTER all API routes:

```python
from flask import send_from_directory

# Add after all API route definitions, before `if __name__ == "__main__":`
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend-dist")

@app.route("/")
def serve_index():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/<path:path>")
def serve_frontend(path):
    """Serve static files; fallback to index.html for SPA routing."""
    file_path = os.path.join(FRONTEND_DIR, path)
    if os.path.isfile(file_path):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, "index.html")
```

**IMPORTANT**: The catch-all `/<path:path>` must be defined AFTER all API routes. Flask prioritizes static (exact-match) routes over dynamic routes, so `/api/predict` will match before this catch-all.

Also add `send_from_directory` to the Flask import line:
```python
from flask import Flask, request, jsonify, send_file, send_from_directory
```

### Step 5: Generate requirements.txt

Extract ONLY the dependencies needed for the web app (not the full course/dev dependencies):

```
flask>=3.0.0
flask-cors>=4.0.0
torch>=2.0.0
transformers>=4.40.0
pandas>=2.2.3
numpy>=2.2.0
accelerate>=0.27.0
datasets>=2.18.0
evaluate>=0.4.0
tqdm>=4.66.0
scikit-learn>=1.6.0
```

### Step 6: Create Launcher Scripts

**`run.bat`** (Windows — the primary target for teachers). **CRITICAL**: Save with UTF-8 BOM encoding so Chinese Windows cmd can parse Chinese characters. Below is the content — write it with `encoding="utf-8-sig"` (Python) or save as UTF-8 with BOM in your editor:

```batch
@echo off
chcp 65001 >nul
echo ========================================
echo   Your Project Name - Launcher
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Install Python 3.8+ from:
    echo         https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Create venv if needed
if not exist ".venv\" (
    echo [1/3] Creating virtual environment...
    python -m venv .venv
)

:: Activate and install
call .venv\Scripts\activate.bat
echo [2/3] Installing dependencies (first time may take 2-5 min)...
pip install -r requirements.txt -q

:: Start
echo [3/3] Starting server...
echo.
echo ========================================
echo   Open browser at: http://localhost:5000
echo   Press Ctrl+C to stop
echo ========================================
echo.
cd backend
python app.py
pause
```

**`run.sh`** (Linux/macOS):

```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d ".venv" ]; then
    echo "[1/3] Creating virtual environment..."
    python3 -m venv .venv
fi
source .venv/bin/activate
echo "[2/3] Installing dependencies..."
pip install -r requirements.txt -q
echo "[3/3] Starting server..."
cd backend
python3 app.py
```

### Step 7: Write a Delivery-Focused README

The README should answer:
1. **What is this?** - One-sentence project description
2. **Requirements** - Just "Python 3.8+"
3. **How to run** - "Double-click run.bat" or `./run.sh`
4. **Where to open** - `http://localhost:5000`
5. **What to expect** - Features available
6. **Troubleshooting** - Port conflicts, slow first load, GPU vs CPU

### Step 8: Package as ZIP

Use Python's `zipfile` to create the delivery ZIP (since `zip` may not be installed in WSL):

```python
import zipfile, os

src = os.path.expanduser("~/submission-dir")
dst = "/path/to/项目名称_交付包.zip"

def add_to_zip(zipf, path, base=""):
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        arcname = os.path.join(base, item) if base else item
        if os.path.isfile(item_path):
            if "__pycache__" in arcname:
                continue
            zipf.write(item_path, arcname)
        elif os.path.isdir(item_path) and item not in ("__pycache__",):
            add_to_zip(zipf, item_path, arcname)

with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zipf:
    add_to_zip(zipf, src)

# Verify
with zipfile.ZipFile(dst, "r") as z:
    bad = z.testzip()
    print(f"Integrity: {'PASS' if bad is None else f'FAIL: {bad}'}")
print(f"Created: {dst} ({os.path.getsize(dst) / 1024 / 1024:.0f} MB)")
```

## Verification Checklist

Before delivering, verify:

- [ ] ZIP integrity passes (`testzip()`)
- [ ] Model weights are included (not excluded by .gitignore)
- [ ] `run.bat` starts cleanly on a fresh Windows machine
- [ ] Frontend loads at `http://localhost:5000` (no separate port)
- [ ] API calls work (single prediction, batch, model info)
- [ ] No `.venv`, `.git`, `node_modules`, `__pycache__` in the ZIP
- [ ] Frontend API calls use relative paths (`/api/...`), not absolute URLs

## Common Pitfalls

### 1. Frontend uses absolute API URL (e.g., `http://localhost:5000/api/...`)

When serving the built frontend from Flask (same origin), absolute URLs still work but break if the port changes. Best practice is to use relative paths (`/api/...`) in the frontend API code.

### 2. Vite proxy config is NOT packaged

The `vite.config.js` proxy (`/api -> localhost:5000`) is only for development. The production build does NOT include the proxy - Flask must serve both the frontend and handle API calls on the same port.

### 3. pip install fails on Windows due to missing C++ build tools

`transformers` and `torch` may need MSVC build tools on Windows. Mitigations:
- Use pre-built wheels (PyTorch official has Windows wheels)
- Recommend the teacher install Python via the official installer (includes pip + wheels)

### 4. CUDA vs CPU torch

Auto-downloads CUDA version by default on systems with NVIDIA GPUs. Add a note in README: "If you don't have a GPU, PyTorch will automatically use CPU mode."

### 5. Huge ZIP size from model weights

Model weights (safetensors) can be 400MB+. This is normal for a course project. If space is a concern, consider shipping in two parts or using HuggingFace hub with auto-download on first run (but this requires internet on the teacher's machine).

### 6. Flask port conflict (port 5000 in use)

In `backend/config.py`, allow the user to change `port` easily. Add a note in README about modifying `config.py`.

### 7. pip install has dependency conflicts (transformers + torch versions)

Torch and transformers from different eras can conflict. Mitigation:
- Test the full `pip install` sequence on a clean environment before delivery
- Pin specific versions if conflicts arise (use `==` not `>=`)

### 8. run.bat encoding breaks on Chinese Windows (GBK code page 936)

Chinese Windows cmd defaults to GBK (cp936), not UTF-8. If the `.bat` file is written as UTF-8 **without BOM**, Chinese characters in `echo` statements are misinterpreted as commands, the whole script flow breaks, and the user sees garbled errors like `'�环境...' is not recognized`.

**Fix**: Write `run.bat` with UTF-8 BOM (`\xEF\xBB\xBF`) — Python's `encoding="utf-8-sig"` produces this. Alternatively, avoid Chinese entirely and use English-only messages in the batch file to side-step encoding issues completely. Example:

```python
bom = "\ufeff"
content = bom + """@echo off
chcp 65001 >nul
...
"""
with open("run.bat", "w", encoding="utf-8-sig") as f:
    f.write(content)
```

Verification: read back and check `content[:3] == b"\xef\xbb\xbf"`.

### 9. Python module name collision: two files named `config.py`

When the project has **two** modules with the same name (`backend/config.py` AND `model/config.py`), Python's import system causes cascading failures regardless of import order.

**Error pattern 1**: `ImportError: cannot import name 'BACKEND_CONFIG' from 'config' (path/to/model/config.py)` — predictor.py inserts `model/` at `sys.path[0]` before app.py imports `config`.

**Error pattern 2**: `ImportError: cannot import name 'SAVED_MODEL_DIR' from 'config' (path/to/backend/config.py)` — if you import backend config first, Python **caches** it as the `config` module. When `model/inference.py` later does `from config import SAVED_MODEL_DIR`, Python serves the cached backend module instead of re-searching `sys.path`.

**Root cause**: Python caches imported modules by **name**, not by path. Two same-named `.py` files cannot coexist when both need to be imported.

**Correct fix**: Rename one of the files to eliminate the name collision entirely:

```python
# backend/config.py → backend/settings.py
# backend/app.py:
from settings import BACKEND_CONFIG   # ← finds backend/settings.py
from predictor import ...              # ← predictor loads model/inference.py
# model/inference.py:
from config import SAVED_MODEL_DIR     # ← finds model/config.py, no collision
```

This also applies to any other commonly colliding names like `utils.py`, `helpers.py`, or `models.py` across project directories. When in doubt, give each subpackage a unique module name.

### 10. WSL /mnt/ to ~/ large file copy is extremely slow

Copying model weight files (300-500MB safetensors) from `/mnt/e/` (NTFS) to `~/` (WSL ext4) using `cp` can **time out** because WSL reads the entire file from NTFS over 9p protocol, then writes it to ext4 — a slow two-way pipe.

**Fix**: Instead of copying to `~/` and zipping there, zip directly from the `/mnt/e/` path using Python's `zipfile` module. It writes to NTFS directly (no cross-filesystem copy) and completes in ~40-60 seconds:

```python
import zipfile, os
src = "/mnt/e/path/to/submission"
dst = "/mnt/e/path/to/交付包.zip"
skip = {".venv", "__pycache__", ".git", "node_modules"}
with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
    for dirpath, dirnames, filenames in os.walk(src):
        dirnames[:] = [d for d in dirnames if d not in skip]
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            z.write(fp, os.path.relpath(fp, src))
```

**Anti-pattern**: `cp -r /mnt/e/... ~/deliverable` — the `cp` step bottlenecks on large model files and can time out at 120s+.
