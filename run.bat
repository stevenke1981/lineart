@echo off
chcp 65001 >nul 2>&1
title Lineart - Anime Character Design Prompt Generator

:: ────────────────────────────────────────────────────────────────────────
:: Lineart One-Click Launcher (Windows)
:: 自動建立虛擬環境、安裝依賴、啟動 Flask Web 伺服器
:: ────────────────────────────────────────────────────────────────────────

setlocal enabledelayedexpansion

set "VENV_DIR=.venv"
set "REQUIREMENTS=requirements.txt"

:: ─── 1. 檢查 Python ──────────────────────────────────────────────────
echo.
echo === Lineart - Anime Character Design Prompt Generator ===
echo.
echo [1/5] Checking Python...

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.11+ from:
    echo        https://www.python.org/downloads/
    echo        Make sure to check "Add Python to PATH"
    pause
    exit /b 1
)

python --version 2>&1 | findstr /R "3\.1[1-9] 3\.[2-9][0-9]" >nul
if %errorlevel% neq 0 (
    echo ERROR: Python 3.11+ is required.
    python --version
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo    found %%v

:: ─── 2. 建立虛擬環境 ────────────────────────────────────────────────
echo.
echo [2/5] Setting up virtual environment...

if not exist "%VENV_DIR%\\Scripts\\python.exe" (
    echo    creating virtual environment...
    python -m venv "%VENV_DIR%"
    if !errorlevel! neq 0 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo    done.
) else (
    echo    virtual environment already exists, skipping.
)

:: ─── 3. 升級 pip ─────────────────────────────────────────────────────
echo.
echo [3/5] Upgrading pip...
"%VENV_DIR%\\Scripts\\python.exe" -m pip install --upgrade pip -q
if !errorlevel! neq 0 (
    echo    warning: pip upgrade failed, continuing...
)

:: ─── 4. 安裝依賴 ─────────────────────────────────────────────────────
echo.
echo [4/5] Installing dependencies...
if exist "%REQUIREMENTS%" (
    "%VENV_DIR%\\Scripts\\pip.exe" install -r "%REQUIREMENTS%" -q
    if !errorlevel! neq 0 (
        echo ERROR: Dependency installation failed.
        pause
        exit /b 1
    )
    echo    dependencies installed.
) else (
    echo WARNING: requirements.txt not found, skipping.
)

:: ─── 5. 啟動 Web 伺服器 ─────────────────────────────────────────────
echo.
echo [5/5] Starting Lineart Web UI...
echo.
echo   http://localhost:5000
echo   Press Ctrl+C to stop the server.
echo.

:: 啟動 Flask 並在背景開啟瀏覽器
start "" "http://localhost:5000"
"%VENV_DIR%\\Scripts\\python.exe" app.py

echo.
echo Server stopped (errorlevel: %errorlevel%)
pause
endlocal
