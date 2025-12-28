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

echo Setting up Python environment (uv preferred)...
if not exist ".venv" (
    where uv >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        echo Creating uv venv...
        uv venv
    ) else (
        echo Creating Python venv...
        py -m venv .venv
    )
)

set VENV_PY=%CD%\.venv\Scripts\python.exe
if not exist "%VENV_PY%" (
    echo Error: venv python not found at %VENV_PY%
    exit /b 1
)

echo Ensuring test dependencies are installed...
where uv >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Using uv to install test requirements...
    uv pip install --python "%VENV_PY%" -r ..\requirements-test.txt
) else (
    echo Using pip to install test requirements...
    "%VENV_PY%" -m pip install -r ..\requirements-test.txt
)

echo Running unit tests...
echo -----------------------------------

REM Run pytest with verbose output
"%VENV_PY%" -m pytest tests\ -v --tb=short

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
