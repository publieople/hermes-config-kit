@echo off
chcp 65001 >nul 2>&1
title {{PROJECT_NAME}} - Windows Deployment
color 0A

echo.
echo ============================================================
echo    {{PROJECT_NAME}} - Windows One-Click Deployment
echo ============================================================
echo.

:: Check admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Please run as Administrator
    echo Right-click deploy.bat → "Run as administrator"
    pause
    exit /b 1
)

echo [1/6] Checking environment...
echo.

:: Check Python
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python not found. Install Python 3.8+ first.
    echo Download: https://www.python.org/downloads/
    echo IMPORTANT: Check "Add Python to PATH" during installation
    pause
    exit /b 1
)
echo [OK] Python installed

:: Check pip
pip --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] pip not found. Reinstall Python with pip enabled.
    pause
    exit /b 1
)
echo [OK] pip available
echo.

echo [2/6] Creating virtual environment...
if exist venv (
    echo [INFO] Virtual environment already exists, skipping
) else (
    python -m venv venv
    if %errorLevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
)
echo.

echo [3/6] Installing dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip >nul 2>&1

if exist requirements.txt (
    pip install -r requirements.txt
) else (
    echo [WARN] No requirements.txt found
)

if %errorLevel% neq 0 (
    echo [ERROR] Dependency installation failed
    echo [TIP] Try: pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

echo [4/6] Checking models/data...
:: Add project-specific checks here
:: e.g., if not exist models\model.pkl ( python train.py )
echo [OK] Ready
echo.

echo [5/6] Configuring environment...
if not exist .env (
    echo [INFO] Creating default .env file
    (
        echo PORT={{DEFAULT_PORT}}
        echo LOG_LEVEL=INFO
    ) > .env
    echo [OK] Created .env — edit if needed
) else (
    echo [OK] .env already exists
)
echo.

echo [6/6] Starting service...
echo.
echo ============================================================
echo    Deployment complete! Starting {{PROJECT_NAME}}...
echo    URL: http://localhost:{{DEFAULT_PORT}}
echo ============================================================
echo.
echo Press Ctrl+C to stop
echo.

:: Load env vars
for /f "tokens=1,2 delims==" %%a in (.env) do (
    set %%a=%%b
)

python {{MAIN_SCRIPT}}

pause
