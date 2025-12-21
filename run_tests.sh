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

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo "pytest not found. Installing test dependencies..."
    
    # Check if uv is available
    if command -v uv &> /dev/null; then
        echo "Using uv to install dependencies..."
        uv pip install pytest
    else
        echo "Using pip to install dependencies..."
        pip install pytest
    fi
fi

echo "Running unit tests..."
echo "-----------------------------------"

# Run pytest with verbose output
pytest tests/ -v --tb=short

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
