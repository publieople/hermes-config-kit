---
name: python-production-deployment
description: "Deploy Python applications to production on Linux (systemd) and Windows (NSSM). Covers service unit design, watchdog scripts, cron health checks, env-file config separation, .bat/.ps1 deployment scripts, Windows service registration, packaging workflows, and minimal API extraction."
version: 1.0.0
author: Hermes Agent
tags: [linux, windows, deployment, systemd, nssm, service, watchdog, production, packaging, python]
---

# Python Production Deployment

Deploy Python applications as production-grade services on Linux (systemd) or Windows (NSSM). Covers auto-start, crash recovery, health monitoring, and packaging for distribution.

## When to Use

- User asks for "开机自启" / auto-start on boot (Linux: Raspberry Pi, Ubuntu Server; Windows: server machines)
- Application needs to run as a background service 24/7
- Need to package a Python project for distribution to non-technical users
- Project developed on Linux/WSL needs Windows deployment
- The user asks "how do I make this production-ready?"

## Architecture Overview

```
┌─────────────────────────┐     ┌──────────────────────────┐
│     Linux (systemd)     │     │     Windows (NSSM)       │
├─────────────────────────┤     ├──────────────────────────┤
│ systemd service unit    │     │ NSSM service registration│
│ EnvironmentFile (.env)  │     │ .bat + .ps1 scripts      │
│ bash watchdog (cron)    │     │ deploy + package scripts │
│ install.sh              │     │ Minimal inference server  │
└─────────────────────────┘     └──────────────────────────┘
```

Pick the platform section that matches your target OS. Both sections share the same principles: separate config from code, auto-restart on failure, health monitoring, and one-command install.

---

## Linux Deployment (systemd)

### Core Pattern

4 layers of reliability:

```
┌─────────────────────┐
│   cron / systemd    │  ← Periodic health checks (every 5 min)
│   timer             │
├─────────────────────┤
│   watchdog.sh       │  ← Lightweight bash health monitor
├─────────────────────┤
│   python app.py     │  ← The application
├─────────────────────┤
│   systemd service   │  ← Auto-start, crash recovery, env config
└─────────────────────┘
```

### 1. Systemd Service Unit Template

```ini
[Unit]
Description={{SERVICE_DESCRIPTION}}
Documentation=https://github.com/owner/repo
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
EnvironmentFile={{INSTALL_DIR}}/{{APP_NAME}}.env
ExecStart=/usr/bin/python3 {{INSTALL_DIR}}/{{MAIN_SCRIPT}} \
    --server ${SERVER_IP} \
    --port ${PORT}
WorkingDirectory={{INSTALL_DIR}}
Restart=on-failure
RestartSec=10
StartLimitBurst=5
StartLimitIntervalSec=120

# Security hardening (optional — may interfere with data dirs)
NoNewPrivileges=true
# ProtectSystem=full        # Uncomment if app writes to /var/lib/
# PrivateTmp=yes

# Logging
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 2. Key Fields Explained

| Field | Value | Why |
|-------|-------|-----|
| `After=network-online.target` | Required for network-dependent apps | Waits for actual network connectivity |
| `Restart=on-failure` | Standard | Restarts on crash, NOT on manual `systemctl stop` |
| `RestartSec=10` | 10-30s typical | Prevents tight restart loops |
| `StartLimitBurst=5` / `StartLimitIntervalSec=120` | Protection | 5 crashes in 2 min → stop trying |
| `EnvironmentFile=` | Path to env config | Separates config from code |

### 3. Service Management Commands

```bash
sudo cp myapp.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable myapp     # Auto-start on boot
sudo systemctl start myapp      # Start NOW
sudo systemctl status myapp
sudo journalctl -u myapp -f     # Follow logs
sudo systemctl restart myapp    # After config change
```

### 4. Environment File

```bash
# {{INSTALL_DIR}}/{{APP_NAME}}.env
# Edit this file to change settings — no need to touch the service

SERVER_IP=192.168.1.100
SERVER_PORT=8888
DURATION=60
INTERVAL=1
OUTPUT_DIR=/var/lib/myapp/data
```

**Syntax rules**: `KEY=value` one per line. No `export` keyword. No spaces around `=`.
Values are NOT shell-expanded by default. Comments start with `#`.

### 5. Watchdog Script (Bash)

A lightweight, zero-dependency health monitor for daemon processes. See `templates/watchdog.sh` for the full template.

**Checks performed at each interval:**
1. Process alive? → restart
2. Memory > threshold? → warn in logs
3. Disk > threshold? → warn in logs
4. Output files stale? → restart (for data-producing apps)
5. Service active? → restart

**Cron installation** (never use `crontab -e` for system services — use `/etc/cron.d/`):

```bash
cat > /etc/cron.d/myapp-watchdog << 'EOF'
SHELL=/bin/bash
*/5 * * * * root /opt/myapp/deploy/watchdog.sh > /dev/null 2>&1
EOF
sudo chmod 644 /etc/cron.d/myapp-watchdog
```

### 6. Install Script

See `templates/install.sh` for the full template that combines everything into a single deploy script.

### 7. Long-Running Test Plan

For services that need to run 24h+:

| Fault to inject | Expected behavior |
|---|---|
| Kill the process | systemd restarts within 10s |
| Unplug network | App logs errors, watchdog detects stall → restart |
| Fill disk | Watchdog warns at 90% |
| Reboot device | Service starts automatically |

**Call it stable when:**
- 72 hours without manual intervention
- Memory stable (±10% of initial RSS)
- Zero watchdog-triggered restarts
- Recovery successful after each fault injection

### 8. Linux Pitfalls

1. **Env file syntax**: No spaces around `=`, no `export` keyword
2. **ProtectSystem blocks writes**: Use `ReadWritePaths=/var/lib/myapp/` if the app writes data
3. **WorkingDirectory**: Set if the app uses relative paths
4. **StartLimitBurst**: After 5 crashes in 2 min, reset with `systemctl reset-failed myapp`
5. **USB/ALSA reconnection**: Watchdog should restart service if USB device disconnects
6. **Cron file permissions**: `/etc/cron.d/*` files must be `chmod 644` or cron silently ignores them

### 9. Linux Verification

```bash
systemctl is-enabled myapp         # → enabled
systemctl is-active myapp          # → active
find /var/lib/myapp/data -mmin -10 | head -5   # producing data
journalctl -t watchdog --since "1 hour ago"     # watchdog running
systemctl show myapp -p NRestarts  # no abnormal restarts
```

---

## Windows Deployment (NSSM)

### Core Patterns

#### Dual Script Strategy
Always provide both `.bat` (batch) and `.ps1` (PowerShell) versions:
- **`.bat`**: Maximum compatibility, no execution policy issues
- **`.ps1`**: Better error handling, progress output

#### Deployment Script Checklist

Every `deploy.bat`/`deploy.ps1` should:
1. Check prerequisites (Python version, pip)
2. Create virtual environment: `python -m venv venv`
3. Install dependencies: `pip install -r requirements.txt`
4. Check/build models
5. Create default config: `.env` file
6. Verify services (with graceful fallback)
7. Start the application

#### Windows Service Registration (NSSM)

```batch
:: Install service
nssm install ServiceName "C:\path\to\venv\Scripts\python.exe"
nssm set ServiceName AppDirectory "C:\path\to\project"
nssm set ServiceName AppParameters "main.py"
nssm set ServiceName Start SERVICE_AUTO_START
nssm set ServiceName Description "Service description"

:: Set environment variables
nssm set ServiceName AppEnvironmentExtra "KEY=value"

:: Start service
net start ServiceName
```

**NSSM installation**: Download from https://nssm.cc/download, extract, copy `nssm.exe` to `C:\Windows\System32\`

#### Packaging Workflow

Create a `package.bat`/`package.ps1` that:
1. Copies source code from development directory
2. Copies data/models directories
3. Copies deployment scripts
4. Creates empty directories (logs, output, etc.)
5. Compresses to `.zip` for distribution

**Important**: Pull from actual source repo, not from deployment tools directory.

#### Path Handling (WSL → Windows)

When creating deployment packages from WSL:
- Write files to `/mnt/X/path/` (Windows filesystem)
- Use Windows-style paths in scripts (`C:\path\to\...` or `%~dp0`)
- Use `chcp 65001` at top of batch files for UTF-8
- Test path variables with `echo %VAR%` before use

#### Windows Project Structure

```
ProjectName-Windows-Deploy/
├── deploy.bat                    # One-click deployment (batch)
├── deploy.ps1                    # One-click deployment (PowerShell)
├── start.bat                     # Quick start script
├── install-service.bat           # NSSM service registration
├── package.bat                   # Packaging script (batch)
├── package.ps1                   # Packaging script (PowerShell)
├── DEPLOY-Windows.md             # Detailed deployment docs
├── README.md                     # Quick start guide
├── quick-reference.txt           # Quick reference card
├── .env.example                  # Environment variable template
└── .gitignore
```

#### deploy.bat Template

```batch
@echo off
chcp 65001 >nul 2>&1
title ProjectName - Windows Deployment

:: Check admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Run as Administrator
    pause
    exit /b 1
)

:: Check Python
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python not found. Install Python 3.8+
    pause
    exit /b 1
)

:: Create venv, install deps, start app
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
python main.py
```

#### .bat vs .ps1 Differences

| Aspect | .bat | .ps1 |
|--------|------|------|
| Execution policy | Always works | May need `Set-ExecutionPolicy` |
| Error handling | `if %errorLevel% neq 0` | `try/catch`, `$LASTEXITCODE` |
| Colors | `color 0A` | `Write-Host -ForegroundColor` |
| Variables | `%VAR%` | `$var` |
| Loops | `for /f` | `foreach` |

#### Minimal API Extraction Pattern

When a bloated Flask/Python API (500+ lines) needs Windows deployment but the user only needs inference:

**Steps:**
1. Identify the core pipeline: data→prediction→response chain
2. Copy only inference functions (model loading, feature extraction, predict)
3. Hard-code defaults instead of database lookups (inline dicts)
4. Keep it under 150 lines
5. Name clearly: `win_server.py` or `infer_server.py`

**What to NOT include in minimal version:**
- Database connections or fallback logic
- Batch processing endpoints
- Statistics/aggregation endpoints
- Data write-back

**Validation**: Run the minimal server and verify it returns same prediction as full server for identical inputs.

See `templates/minimal_flask_inference.py` for a ~100-line template.

#### Windows Pitfalls

1. **PowerShell Execution Policy**: Users may need `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`
2. **Python Not in PATH**: Most common issue — users forget "Add Python to PATH"
3. **Port Conflicts**: `netstat -ano | findstr :5000`
4. **Database Fallback**: Design to work WITHOUT database initially (local JSON mode)
5. **NSSM Download**: May fail behind Chinese networks — provide manual download instructions
6. **Path Quotes**: Always quote paths in batch: `set "CURRENT_DIR=%~dp0"`

#### Windows Verification

```cmd
curl http://localhost:5000/health
sc query ServiceName
nssm status ServiceName
```

### Distribution

Final delivery is a `.zip` file containing:
- All source code
- Pre-trained models (if applicable)
- Sample data
- Deployment scripts
- Documentation

User extracts and runs `deploy.bat` as Administrator.

---

## Support Files

### References (session-specific detail)

- `references/deploy-patterns.md` — Linux deployment session trace with design rationale and team collaboration details
- `references/nssm-reference.md` — NSSM commands reference (service install, config, logs, troubleshooting)

### Templates (reusable with PLACEHOLDERS)

- `templates/service-unit.service` — systemd unit template with {{SERVICE_DESCRIPTION}}, {{APP_NAME}}, {{INSTALL_DIR}}, {{MAIN_SCRIPT}} placeholders
- `templates/watchdog.sh` — general-purpose bash watchdog with process/memory/disk/staleness checks
- `templates/install.sh` — one-command install script (copy source → env file → systemd → cron)
- `templates/deploy.bat` — Reusable deploy.bat template with {{PLACEHOLDERS}}
- `templates/minimal_flask_inference.py` — Minimal Flask inference server template (~100 lines, input→predict→JSON output)
