#!/usr/bin/env python3
"""
Build script for creating distributable bundles of the media player application.
This script:
1. Builds the frontend (npm run build)
2. On Windows: Creates a PyInstaller executable bundle with the built frontend
3. On Unix: Creates a simple distribution package

Usage:
    python build.py [--skip-frontend] [--skip-bundle]
"""

import argparse
import importlib.util
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_step(message):
    """Print a step message in blue"""
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}► {message}{Colors.ENDC}")


def print_success(message):
    """Print a success message in green"""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_error(message):
    """Print an error message in red"""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}", file=sys.stderr)


def print_warning(message):
    """Print a warning message in yellow"""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")


def run_command(cmd, cwd=None, shell=False):
    """Run a command and return the result"""
    try:
        # On Windows, when using shell=True, `subprocess.run()` expects a string command.
        # This is particularly important for tools like `npm` which are often `npm.cmd`.
        if shell and isinstance(cmd, (list, tuple)):
            cmd = subprocess.list2cmdline(list(cmd))
        result = subprocess.run(
            cmd,
            cwd=cwd,
            shell=shell,
            check=True,
            capture_output=True,
            text=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr
    except FileNotFoundError as e:
        return False, str(e)


def remove_tree_with_retries(path: Path, retries: int = 5, delay_seconds: float = 1.0) -> bool:
    """Remove a directory tree, retrying on Windows file-lock errors."""
    if not path.exists():
        return True

    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            shutil.rmtree(path)
            return True
        except PermissionError as e:
            last_error = e
            if attempt < retries:
                time.sleep(delay_seconds)
            else:
                break
    print_error(f"Failed to remove directory {path}: {last_error}")
    return False


def remove_file_with_retries(path: Path, retries: int = 5, delay_seconds: float = 1.0) -> bool:
    """Remove a file, retrying on Windows file-lock errors."""
    if not path.exists():
        return True

    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            path.unlink()
            return True
        except PermissionError as e:
            last_error = e
            if attempt < retries:
                time.sleep(delay_seconds)
            else:
                break
    print_warning(f"Could not remove file {path}: {last_error}")
    return False


def check_node_installed():
    """Check if Node.js is installed"""
    success, _ = run_command(['node', '--version'])
    return success


def check_npm_installed():
    """Check if npm is installed"""
    # On Windows, npm is typically a `.cmd` shim; using shell=True makes it reliably runnable.
    is_windows = platform.system() == 'Windows'
    success, _ = run_command(['npm', '--version'], shell=is_windows)
    return success


def build_frontend(frontend_dir):
    """Build the frontend using npm"""
    print_step("Building frontend...")

    is_windows = platform.system() == 'Windows'
    
    if not check_node_installed():
        print_error("Node.js is not installed. Please install Node.js to build the frontend.")
        return False
    
    if not check_npm_installed():
        print_error("npm is not installed. Please install npm to build the frontend.")
        return False
    
    # Install dependencies if node_modules doesn't exist
    node_modules = frontend_dir / 'node_modules'
    if not node_modules.exists():
        print("Installing frontend dependencies...")
        success, output = run_command(['npm', 'install'], cwd=frontend_dir, shell=is_windows)
        if not success:
            print_error(f"Failed to install frontend dependencies:\n{output}")
            return False
        print_success("Frontend dependencies installed")
    
    # Build the frontend
    print("Running npm build...")
    success, output = run_command(['npm', 'run', 'build'], cwd=frontend_dir, shell=is_windows)
    if not success:
        print_error(f"Frontend build failed:\n{output}")
        return False
    
    # Check if static folder was created
    static_dir = frontend_dir.parent / 'backend' / 'static'
    if not static_dir.exists():
        print_error(f"Build succeeded but static folder not found at {static_dir}")
        return False
    
    print_success(f"Frontend built successfully to {static_dir}")
    return True


def bundle_with_pyinstaller(backend_dir):
    """Bundle the application using PyInstaller (Windows only)"""
    print_step("Creating executable bundle with PyInstaller...")
    
    is_windows = platform.system() == 'Windows'
    
    if not is_windows:
        print_warning("PyInstaller bundling is designed for Windows. Skipping on Unix systems.")
        return True

    # Ensure backend runtime dependencies are available in the build environment.
    # PyInstaller bundles what it can import/resolve from the current interpreter.
    requirements_file = backend_dir / 'requirements.txt'
    if requirements_file.exists():
        print("Installing backend dependencies (requirements.txt)...")
        success, output = run_command([sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)])
        if not success:
            print_error(f"Failed to install backend dependencies:\n{output}")
            return False
        print_success("Backend dependencies installed")
    else:
        print_warning(f"requirements.txt not found at {requirements_file}; continuing without installing backend deps")
    
    # Check if PyInstaller is installed using importlib for robustness
    pyinstaller_spec = importlib.util.find_spec('PyInstaller')
    
    if pyinstaller_spec is None:
        print_warning("PyInstaller is not installed.")
        print("Installing PyInstaller...")
        success, output = run_command([sys.executable, '-m', 'pip', 'install', 'pyinstaller>=6.0.0'])
        if not success:
            print_error(f"Failed to install PyInstaller:\n{output}")
            return False
        print_success("PyInstaller installed")
    
    # Check if spec file exists
    spec_file = backend_dir / 'media-player.spec'
    if not spec_file.exists():
        print_error(f"PyInstaller spec file not found at {spec_file}")
        return False
    
    # Clean previous build
    dist_dir = backend_dir / 'dist'
    build_dir = backend_dir / 'build'

    # For one-file builds, the primary output is dist/media-player.exe.
    # Try removing just the output exe first to avoid deleting dist/ when it is held open.
    remove_file_with_retries(dist_dir / 'media-player.exe')
    remove_file_with_retries(dist_dir / 'media-player' / 'media-player.exe')
    
    if dist_dir.exists():
        print(f"Cleaning previous build in {dist_dir}...")
        if not remove_tree_with_retries(dist_dir):
            print_warning(
                "Could not fully remove dist directory (it may be open in Explorer or locked by AV). "
                "Continuing build; if PyInstaller fails, close any processes using backend/dist and retry."
            )
    
    if build_dir.exists():
        print(f"Cleaning build directory {build_dir}...")
        if not remove_tree_with_retries(build_dir):
            print_warning(
                "Could not fully remove build directory (it may be locked). "
                "Continuing build; if PyInstaller fails, close any processes using backend/build and retry."
            )
    
    # Run PyInstaller
    print("Running PyInstaller...")
    success, output = run_command(
        [sys.executable, '-m', 'PyInstaller', '--noconfirm', str(spec_file)],
        cwd=backend_dir
    )
    
    if not success:
        print_error(f"PyInstaller build failed:\n{output}")
        return False
    
    # Check if the executable was created
    # One-file build: dist/media-player.exe
    # One-dir build (legacy): dist/media-player/media-player.exe
    onefile_exe_path = dist_dir / 'media-player.exe'
    onedir_exe_path = dist_dir / 'media-player' / 'media-player.exe'

    if onefile_exe_path.exists():
        print_success(f"Executable created at {onefile_exe_path}")
        print(f"\n{Colors.OKGREEN}The application can be distributed by sharing this single file:")
        print(f"  {onefile_exe_path}{Colors.ENDC}")
        return True

    if onedir_exe_path.exists():
        print_success(f"Executable bundle created at {dist_dir / 'media-player'}")
        print(f"\n{Colors.OKGREEN}The application can be distributed by sharing the entire folder:")
        print(f"  {dist_dir / 'media-player'}{Colors.ENDC}")
        return True

    print_error(f"Executable not found at {onefile_exe_path} or {onedir_exe_path}")
    return False
    


def create_unix_distribution(project_root, backend_dir):
    """Create a distribution package for Unix systems"""
    print_step("Creating Unix distribution package...")
    
    dist_dir = project_root / 'dist'
    dist_package = dist_dir / 'media-player-unix'
    
    # Clean previous distribution
    if dist_package.exists():
        print(f"Cleaning previous distribution in {dist_package}...")
        shutil.rmtree(dist_package)
    
    dist_package.mkdir(parents=True, exist_ok=True)
    
    # Copy backend files
    backend_dist = dist_package / 'backend'
    print("Copying backend files...")
    shutil.copytree(
        backend_dir,
        backend_dist,
        ignore=shutil.ignore_patterns(
            '__pycache__', '*.pyc', '*.pyo', '.venv', 'venv',
            'dist', 'build', '*.spec', '.pytest_cache',
            'test_*.py', 'tests', '*_test.py'
        )
    )
    
    # Create a README for the distribution
    readme_content = """# Media Player Distribution

This package includes the Media Player application with a pre-built frontend.

## Installation

1. Install Python 3.13
2. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

   Or using uv (faster):
   ```bash
   cd backend
   pip install uv
   uv sync --no-build-isolation
   ```

## Running the Application

```bash
cd backend
python app.py
```

Or with uv:
```bash
cd backend
uv run python app.py
```

Then open your browser and navigate to http://localhost:5000

The web interface is already built and included in the `static/` folder.

## Requirements

- Python 3.13
- pip (or uv)

## Features

- Pre-built web interface (no Node.js required)
- Network storage support (SMB/CIFS, NFS)
- Playlist management
- Advanced playback controls with crossfade

## Documentation

For detailed documentation, visit: https://github.com/xXLAOKOONXx/media-player
"""
    
    with open(dist_package / 'README.md', 'w') as f:
        f.write(readme_content)
    
    print_success(f"Unix distribution package created at {dist_package}")
    print(f"\n{Colors.OKGREEN}The application can be distributed by sharing the entire folder:")
    print(f"  {dist_package}{Colors.ENDC}")
    
    return True


def main():
    """Main build script"""
    parser = argparse.ArgumentParser(
        description='Build distributable bundles for the media player application'
    )
    parser.add_argument(
        '--skip-frontend',
        action='store_true',
        help='Skip building the frontend (assumes it is already built)'
    )
    parser.add_argument(
        '--skip-bundle',
        action='store_true',
        help='Skip creating the executable bundle (only build frontend)'
    )
    
    args = parser.parse_args()
    
    # Determine project structure
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir
    backend_dir = project_root / 'backend'
    frontend_dir = project_root / 'frontend'
    
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("=" * 60)
    print("  Media Player Build Script")
    print("=" * 60)
    print(f"{Colors.ENDC}")
    print(f"\nProject root: {project_root}")
    print(f"Platform: {platform.system()}")
    print(f"Python: {sys.version.split()[0]}")
    
    # Build frontend
    if not args.skip_frontend:
        if not build_frontend(frontend_dir):
            print_error("\nBuild failed during frontend build step")
            sys.exit(1)
    else:
        print_warning("Skipping frontend build (--skip-frontend specified)")
        # Check if static folder exists
        static_dir = backend_dir / 'static'
        if not static_dir.exists():
            print_error(f"Static folder not found at {static_dir}. Cannot skip frontend build.")
            sys.exit(1)
    
    # Create bundle
    if not args.skip_bundle:
        is_windows = platform.system() == 'Windows'
        
        if is_windows:
            if not bundle_with_pyinstaller(backend_dir):
                print_error("\nBuild failed during PyInstaller bundling step")
                sys.exit(1)
        else:
            if not create_unix_distribution(project_root, backend_dir):
                print_error("\nBuild failed during Unix distribution creation")
                sys.exit(1)
    else:
        print_warning("Skipping bundle creation (--skip-bundle specified)")
    
    print(f"\n{Colors.OKGREEN}{Colors.BOLD}✓ Build completed successfully!{Colors.ENDC}\n")


if __name__ == '__main__':
    main()
