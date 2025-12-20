@echo off
REM Build script for Windows
REM This script builds the frontend and creates a Windows executable bundle

echo ========================================
echo   Media Player Build Script (Windows)
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Run the build script
python build.py %*

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
