#!/bin/bash
# Build script for Unix/Linux/macOS
# This script builds the frontend and creates a distribution package

set -e

echo "========================================"
echo "  Media Player Build Script (Unix)"
echo "========================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Run the build script
python3 build.py "$@"

echo ""
echo "Build completed successfully!"
echo ""
