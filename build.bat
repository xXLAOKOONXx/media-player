@echo off
REM Build script for Windows
REM This script builds the frontend and creates a Windows executable bundle

echo ========================================
echo   Media Player Build Script (Windows)
echo ========================================
echo.

REM Prefer Python 3.13 via the Python Launcher (py). Fallback to python on PATH.
set "PYTHON_CMD="

py -3.13 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3.13"
) else (
    python --version >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_CMD=python"
    )
)

if "%PYTHON_CMD%"=="" (
    echo Error: Python 3.13 is not available.
    echo Please install Python 3.13 or ensure it is available via `py -3.13`.
    pause
    exit /b 1
)

REM Run the build script
%PYTHON_CMD% build.py %*

if errorlevel 1 (
    echo.
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo Build completed successfully!
echo.
pause
