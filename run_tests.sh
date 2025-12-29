#!/bin/bash
# Test runner script for media player backend

set -e

echo "=================================="
echo "Media Player - Test Suite"
echo "=================================="
echo ""

# Change to the script's directory
cd "$(dirname "$0")"

# Check if backend directory exists
if [ ! -d "backend" ]; then
    echo "Error: backend directory not found"
    exit 1
fi

cd backend

echo "Ensuring test dependencies are installed (uv preferred)..."
if command -v uv &> /dev/null; then
    uv sync --extra dev
    echo "Running unit tests..."
    echo "-----------------------------------"
    uv run pytest tests/ -v --tb=short
else
    echo "Warning: uv not found; falling back to venv + pip + requirements-test.txt"

    # Create a venv if it doesn't exist
    if [ ! -d ".venv" ]; then
        python -m venv .venv
    fi

    # Pick venv python (support POSIX and Windows Git Bash)
    if [ -x ".venv/bin/python" ]; then
        VENV_PY=".venv/bin/python"
    elif [ -f ".venv/Scripts/python.exe" ]; then
        VENV_PY=".venv/Scripts/python.exe"
    else
        echo "Error: venv python not found"
        exit 1
    fi

    "$VENV_PY" -m pip install -r ../requirements-test.txt

    echo "Running unit tests..."
    echo "-----------------------------------"
    "$VENV_PY" -m pytest tests/ -v --tb=short
fi

TEST_EXIT_CODE=$?

echo ""
echo "=================================="
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✓ All tests passed!"
else
    echo "✗ Some tests failed"
fi
echo "=================================="

exit $TEST_EXIT_CODE
