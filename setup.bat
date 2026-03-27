@echo off
title India Election Monitor — Python Setup
color 0A
echo.
echo  =====================================================
echo   India Election Monitor 2026 — Auto Setup
echo  =====================================================
echo.

:: ── Step 1: Search for Python installations ───────────────────────
echo [1/5] Searching for Python on your system...
echo.

set PYTHON_EXE=
set PIP_EXE=

:: Check common install locations
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python39\python.exe"
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
    "C:\Program Files\Python313\python.exe"
    "C:\Program Files\Python312\python.exe"
    "C:\Program Files\Python311\python.exe"
    "C:\Program Files\Python310\python.exe"
    "C:\Program Files (x86)\Python313\python.exe"
    "C:\Program Files (x86)\Python312\python.exe"
    "C:\Program Files (x86)\Python311\python.exe"
) do (
    if exist %%P (
        set PYTHON_EXE=%%~P
        goto :found_python
    )
)

:: Try Windows Store Python
for %%P in (
    "%LOCALAPPDATA%\Microsoft\WindowsApps\python3.exe"
    "%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe"
) do (
    if exist %%P (
        set PYTHON_EXE=%%~P
        goto :found_python
    )
)

:: Try 'where' command as last resort
for /f "delims=" %%i in ('where python 2^>nul') do (
    set PYTHON_EXE=%%i
    goto :found_python
)
for /f "delims=" %%i in ('where python3 2^>nul') do (
    set PYTHON_EXE=%%i
    goto :found_python
)
for /f "delims=" %%i in ('where py 2^>nul') do (
    set PYTHON_EXE=%%i
    goto :found_python
)

:: Not found
echo  [ERROR] Python was not found on your system.
echo.
echo  Please install Python 3.11+ from: https://python.org/downloads
echo  IMPORTANT: During install, check "Add Python to PATH"
echo.
pause
exit /b 1

:found_python
echo  [OK] Found Python at: %PYTHON_EXE%
echo.

:: ── Step 2: Get Python version ─────────────────────────────────────
echo [2/5] Python version:
"%PYTHON_EXE%" --version
echo.

:: ── Step 3: Add Python to current session PATH ────────────────────
echo [3/5] Adding Python to PATH for this session...
for %%F in ("%PYTHON_EXE%") do set PYTHON_DIR=%%~dpF
set SCRIPTS_DIR=%PYTHON_DIR%Scripts
set PATH=%PYTHON_DIR%;%SCRIPTS_DIR%;%PATH%
echo  [OK] Added: %PYTHON_DIR%
echo  [OK] Added: %SCRIPTS_DIR%
echo.

:: ── Step 3b: Permanently add to User PATH ─────────────────────────
echo  Adding permanently to your User PATH (no admin needed)...
for /f "skip=2 tokens=3*" %%a in ('reg query HKCU\Environment /v PATH 2^>nul') do set "CURRENT_PATH=%%a %%b"
:: Avoid duplicates
echo %CURRENT_PATH% | find /i "%PYTHON_DIR%" >nul 2>&1
if errorlevel 1 (
    setx PATH "%PYTHON_DIR%;%SCRIPTS_DIR%;%CURRENT_PATH%" >nul
    echo  [OK] PATH updated permanently.
) else (
    echo  [OK] Python already in permanent PATH.
)
echo.

:: ── Step 4: Bootstrap pip if missing ──────────────────────────────
echo [4/5] Checking for pip...
"%PYTHON_EXE%" -m pip --version >nul 2>&1
if errorlevel 1 (
    echo  [!] pip not found — bootstrapping with ensurepip...
    "%PYTHON_EXE%" -m ensurepip --upgrade
    if errorlevel 1 (
        echo  [!] ensurepip failed — downloading get-pip.py fallback...
        powershell -Command "Invoke-WebRequest -Uri https://bootstrap.pypa.io/get-pip.py -OutFile '%TEMP%\get-pip.py'"
        "%PYTHON_EXE%" "%TEMP%\get-pip.py"
    )
    "%PYTHON_EXE%" -m pip --version >nul 2>&1
    if errorlevel 1 (
        echo.
        echo  [ERROR] Could not install pip. Please reinstall Python from:
        echo          https://python.org/downloads
        echo  Make sure to check "Install pip" during setup.
        pause
        exit /b 1
    )
    echo  [OK] pip bootstrapped successfully.
) else (
    echo  [OK] pip is available.
)
echo.

:: ── Step 5: Install dependencies ──────────────────────────────────
echo [5/5] Installing Python packages...
echo  (flask, requests, beautifulsoup4, feedparser, etc.)
echo.
cd /d "%~dp0"
"%PYTHON_EXE%" -m pip install --upgrade pip --quiet
"%PYTHON_EXE%" -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo  [ERROR] pip install failed. Please check your internet connection.
    pause
    exit /b 1
)

:: ── Done ───────────────────────────────────────────────────────────
echo.
echo  =====================================================
echo   Setup complete! Starting the dashboard now...
echo  =====================================================
echo.
echo  Open your browser and go to: http://localhost:5000
echo  Press Ctrl+C to stop the server.
echo.
"%PYTHON_EXE%" app.py
pause
