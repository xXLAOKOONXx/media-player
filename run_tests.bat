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

echo Ensuring test dependencies are installed (uv preferred)...
where uv >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    uv sync --extra dev

    echo Running unit tests...
    echo -----------------------------------
    uv run pytest tests\ -v --tb=short
) else (
    echo Warning: uv not found; falling back to venv + pip + requirements-test.txt

    if not exist ".venv" (
        py -m venv .venv
    )

    set VENV_PY=%CD%\.venv\Scripts\python.exe
    if not exist "%VENV_PY%" (
        echo Error: venv python not found at %VENV_PY%
        exit /b 1
    )

    "%VENV_PY%" -m pip install -r ..\requirements-test.txt

    echo Running unit tests...
    echo -----------------------------------
    "%VENV_PY%" -m pytest tests\ -v --tb=short
)

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
