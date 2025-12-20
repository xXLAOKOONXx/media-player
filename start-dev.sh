#!/bin/bash
set -e

echo "🚀 Starting Media Player Development Environment"
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv package manager..."
    pip install uv
fi

# Install backend dependencies
echo "🐍 Installing backend dependencies with uv..."
cd backend
uv sync --no-build-isolation
cd ..

# Install frontend dependencies
echo "📦 Installing frontend dependencies with npm..."
cd frontend
npm install
echo ""

# Build frontend
echo "🔨 Building frontend..."
npm run build
cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo "  Backend:  cd backend && uv run python app.py"
echo "  Frontend: cd frontend && npm run dev"
echo ""
echo "Or run the backend (which serves the built frontend):"
echo "  cd backend && uv run python app.py"
echo ""

cd backend
echo "🌐 Starting backend server..."
uv run python app.py
