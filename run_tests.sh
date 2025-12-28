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

echo "Setting up Python environment (uv preferred)..."
# Create a venv if it doesn't exist
if [ ! -d ".venv" ]; then
    if command -v uv &> /dev/null; then
        echo "Creating uv venv..."
        uv venv
    else
        echo "Creating Python venv..."
        python -m venv .venv
    fi
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

echo "Ensuring test dependencies are installed..."
# Prefer uv if available to install all test requirements into the venv
if command -v uv &> /dev/null; then
    echo "Using uv to install test requirements..."
    uv pip install --python "$VENV_PY" -r ../requirements-test.txt
else
    echo "Using pip to install test requirements..."
    "$VENV_PY" -m pip install -r ../requirements-test.txt
fi

echo "Running unit tests..."
echo "-----------------------------------"

# Run pytest with verbose output
"$VENV_PY" -m pytest tests/ -v --tb=short

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
