@echo off
setlocal EnableExtensions EnableDelayedExpansion

echo ========================================================
echo        BIST Signal Bot - Windows Startup Script
echo ========================================================
echo.

:: 1. Check Python installation
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ and try again.
    pause
    goto :EOF
)

:: 2. Ensure running from root directory
if not exist "pyproject.toml" (
    echo [ERROR] pyproject.toml not found.
    echo Please run this script from the root directory of the repository.
    pause
    goto :EOF
)

:: 3. Check and Create .venv
if not exist ".venv" (
    echo [INFO] Creating Python virtual environment...
    python -c "import venv; venv.create('.venv', with_pip=True)"
    if !ERRORLEVEL! neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        goto :EOF
    )
)

:: 4. Verify Virtual Environment
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment seems broken. python.exe not found in .venv\Scripts.
    echo Consider deleting the .venv folder and running this script again.
    pause
    goto :EOF
)

:: 5. Upgrade pip, setuptools, wheel
echo [INFO] Upgrading pip, setuptools, wheel...
".venv\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel >nul 2>&1

:: 6. Install dependencies
echo [INFO] Installing dependencies from requirements.txt...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if !ERRORLEVEL! neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    goto :EOF
)

:: 7. Check and Prompt for .env
if not exist ".env" (
    echo [INFO] .env file not found. Copying from .env.example...
    if exist ".env.example" (
        copy .env.example .env >nul
        echo [WARN] .env created from .env.example. Please review settings later.
    ) else (
        echo [WARN] .env.example not found. Creating a minimal .env file.
        echo ENABLE_FINAL_HANDOFF=true> .env
    )
)

:: 8. Create logs directory
if not exist "logs" (
    mkdir logs
)

:: 9. Ensure .gitignore rules
findstr /C:".venv" .gitignore >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo.>> .gitignore
    echo .venv/>> .gitignore
    echo logs/>> .gitignore
    echo .env>> .gitignore
    echo [INFO] Added .venv, logs/, and .env to .gitignore.
)

:: 10. Run Smoke Tests / Healthcheck
echo [INFO] Running Healthcheck...
".venv\Scripts\python.exe" scripts\windows_healthcheck.py > logs\healthcheck.log 2>&1
if !ERRORLEVEL! neq 0 (
    echo [ERROR] Healthcheck failed. See logs\healthcheck.log for details.
    type logs\healthcheck.log
    pause
    goto :EOF
)
echo [INFO] Healthcheck passed.

:: 11. Optional execution (Demo/Start)
echo.
echo [INFO] System is healthy and dependencies are installed.
echo Press any key to run the offline demo (bist_signal_bot bootstrap demo), or close this window to exit.
pause

echo [INFO] Running Offline Demo...
".venv\Scripts\python.exe" -m bist_signal_bot bootstrap demo > logs\runtime.log 2>&1
if !ERRORLEVEL! neq 0 (
    echo [ERROR] Demo failed. See logs\runtime.log for details.
    type logs\runtime.log
    pause
    goto :EOF
)

echo [SUCCESS] Demo completed successfully. See logs\runtime.log for details.
pause
