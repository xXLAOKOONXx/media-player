@echo off
REM Test runner script for media player backend (Windows)

echo ==================================
echo Media Player - Test Suite
echo ==================================
echo.

REM Change to the script's directory
cd /d "%~dp0"

REM Check if backend directory exists
if not exist "backend\" (
    echo Error: backend directory not found
    exit /b 1
)

cd backend

REM Check if pytest is available
where pytest >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo pytest not found. Installing test dependencies...
    
    REM Check if uv is available
    where uv >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        echo Using uv to install dependencies...
        uv pip install pytest
    ) else (
        echo Using pip to install dependencies...
        pip install pytest
    )
)

echo Running unit tests...
echo -----------------------------------

REM Run pytest with verbose output
pytest tests\ -v --tb=short

set TEST_EXIT_CODE=%ERRORLEVEL%

echo.
echo ==================================
if %TEST_EXIT_CODE% EQU 0 (
    echo [92m✓ All tests passed![0m
) else (
    echo [91m✗ Some tests failed[0m
)
echo ==================================

exit /b %TEST_EXIT_CODE%
