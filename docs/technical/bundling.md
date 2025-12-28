# Bundling Guide

This guide explains how to create distributable bundles of the Media Player application.

## Overview

The Media Player supports creating shippable bundles that include the built frontend:

- **Windows**: Creates a standalone executable using PyInstaller
- **Unix/Linux/macOS**: Creates a distribution package with all necessary files

## Prerequisites

### All Platforms
- Python 3.13
- Node.js 14 or higher
- npm

### Windows Only
- PyInstaller will be automatically installed if not present

## Building Bundles

### Automated Build (GitHub Actions)

The easiest way to create a Windows executable is using the automated GitHub Actions workflow:

1. Go to the **Actions** tab in the GitHub repository
2. Select **"Build Windows Executable"**
3. Click **"Run workflow"**
4. (Optional) Enter a version tag
5. Download the artifact when the build completes

See [`.github/README.md`](../.github/README.md) for detailed instructions.

**Benefits:**
- No local build environment needed
- Consistent builds every time
- Automatic artifact storage
- Build logs for troubleshooting

### Local Build

#### Quick Start

##### Windows
```bash
build.bat
```

##### Unix/Linux/macOS
```bash
./build.sh
```

### Manual Build

You can also use the Python build script directly:

```bash
python build.py
```

or on Unix:

```bash
python3 build.py
```

## Build Script Options

The build script supports the following options:

- `--skip-frontend`: Skip building the frontend (assumes it's already built)
- `--skip-bundle`: Only build the frontend, skip creating the bundle

### Examples

Build only the frontend:
```bash
python build.py --skip-bundle
```

Create bundle without rebuilding frontend:
```bash
python build.py --skip-frontend
```

## Output

### Windows

The build process creates a `dist/media-player` folder in the backend directory containing:

```
backend/dist/media-player/
├── media-player.exe          # Main executable
├── static/                   # Built frontend (included)
│   ├── index.html
│   ├── assets/
│   └── ...
└── [Various DLL and dependency files]
```

**To distribute**: Share the entire `dist/media-player` folder. Users can run `media-player.exe` directly.

### Unix/Linux/macOS

The build process creates a `dist/media-player-unix` folder containing:

```
dist/media-player-unix/
├── README.md                 # Distribution instructions
└── backend/
    ├── app.py               # Main application
    ├── static/              # Built frontend (included)
    ├── *.py                 # Backend modules
    └── pyproject.toml       # Dependencies
```

**To distribute**: Share the entire `dist/media-player-unix` folder. See the included README.md for installation instructions.

## Build Process Details

The build script performs the following steps:

1. **Frontend Build**
   - Installs npm dependencies (if needed)
   - Runs `npm run build` in the frontend directory
   - Outputs to `backend/static/`

2. **Backend Bundle (Windows Only)**
   - Installs PyInstaller (if needed)
   - Creates executable using the `media-player.spec` file
   - Includes all frontend static files in the bundle
   - Outputs to `backend/dist/media-player/`

3. **Distribution Package (Unix)**
   - Copies backend files
   - Includes built frontend in `static/` folder
   - Generates README with installation instructions
   - Outputs to `dist/media-player-unix/`

## Platform-Specific Notes

### Windows

#### Console Window
The Windows executable is configured to show a console window. This is useful for debugging and seeing application logs. To hide the console window in production:

1. Edit `backend/media-player.spec`
2. Change `console=True` to `console=False`
3. Rebuild

#### Antivirus False Positives
Some antivirus software may flag PyInstaller executables as suspicious. This is a common false positive. You can:
- Add an exception in your antivirus software
- Sign the executable with a code signing certificate (recommended for distribution)

#### Windows Defender SmartScreen
When running the executable for the first time, Windows may show a SmartScreen warning. Users can click "More info" and then "Run anyway". For production distribution, consider code signing.

### Unix/Linux/macOS

The Unix distribution requires users to:
1. Install Python 3.13
2. Install pip dependencies
3. Run the application with `python app.py`

For a more integrated experience on Unix systems, consider:
- Creating a systemd service (Linux)
- Using a tool like `py2app` for macOS app bundles
- Containerizing with Docker

## Troubleshooting

### Frontend Build Fails

**Problem**: `npm run build` fails

**Solutions**:
- Ensure Node.js and npm are installed: `node --version && npm --version`
- Delete `node_modules` and `package-lock.json`, then rebuild
- Check for disk space issues

### PyInstaller Not Found

**Problem**: PyInstaller is not installed

**Solution**: The script will attempt to install it automatically. If that fails:
```bash
pip install pyinstaller>=6.0.0
```

### Missing Static Files in Bundle

**Problem**: The executable runs but shows "Static folder not found"

**Solutions**:
- Ensure frontend is built before bundling: `python build.py`
- Check that `backend/static/` exists and contains files
- Don't use `--skip-frontend` unless frontend is already built

### Executable Won't Run

**Problem**: Double-clicking the .exe does nothing

**Solutions**:
- Run from command prompt to see error messages
- Check antivirus hasn't quarantined the file
- Ensure all dependencies are included (check `media-player.spec`)

### Large Bundle Size

**Problem**: The Windows bundle is very large

**Solutions**:
- This is normal for PyInstaller bundles (typically 50-100 MB)
- Use UPX compression (enabled by default in the spec file)
- Exclude unnecessary dependencies in `media-player.spec`

## Customizing the Build

### PyInstaller Spec File

The `backend/media-player.spec` file controls how PyInstaller bundles the application. You can customize:

- **Hidden imports**: Add modules that PyInstaller doesn't detect automatically
- **Data files**: Include additional files in the bundle
- **Executable options**: Icon, console visibility, etc.

Example customizations:

#### Add an Icon
```python
exe = EXE(
    # ...
    icon='path/to/icon.ico',  # Add this line
)
```

#### Exclude Console Window
```python
exe = EXE(
    # ...
    console=False,  # Change from True
)
```

#### Include Additional Files
```python
a = Analysis(
    # ...
    datas=[
        *static_files,
        ('extra_file.txt', '.'),  # Add this line
    ],
)
```

### Build Script

The `build.py` script can be modified to add custom build steps:

- Pre-build hooks
- Post-build packaging (e.g., creating ZIP archives)
- Custom file copying
- Version stamping

## Continuous Integration

You can integrate the build process into CI/CD pipelines.

### GitHub Actions (Included)

This repository includes a ready-to-use GitHub Actions workflow for building Windows executables:

**File:** `.github/workflows/build-windows-exe.yml`

**Features:**
- Manual trigger (workflow_dispatch)
- Automated frontend and backend builds
- Artifact upload with retention
- Optional version tagging
- Release notes generation

**To use:**
1. Navigate to Actions tab in GitHub
2. Select "Build Windows Executable"
3. Click "Run workflow"

See [`.github/README.md`](../.github/README.md) for complete documentation.

### Custom CI/CD Example

For automated builds on tags, you can modify the workflow or create a new one:

```yaml
name: Build on Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Build
        run: python build.py
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: media-player-windows-${{ github.ref_name }}
          path: backend/dist/media-player/
```

## Distribution Best Practices

1. **Version Control**: Tag releases in git before building
2. **Testing**: Test the bundle on a clean system before distributing
3. **Documentation**: Include a README with system requirements
4. **Updates**: Provide a mechanism for users to check for updates
5. **Support**: Include contact information for support

## Advanced Topics

### Creating an Installer

For professional distribution, consider creating an installer:

**Windows**:
- Inno Setup
- NSIS
- WiX Toolset

**macOS**:
- py2app + package into .app
- Create DMG installer

**Linux**:
- Create .deb packages (Debian/Ubuntu)
- Create .rpm packages (RedHat/Fedora)
- AppImage for universal Linux distribution

### Code Signing

For production distribution:
- **Windows**: Use SignTool with a code signing certificate
- **macOS**: Use Apple Developer certificate
- **Linux**: GPG sign packages

## FAQ

### Q: Can I cross-compile (e.g., build Windows bundle on Linux)?

**A**: PyInstaller does not support cross-compilation. You must build on the target platform.

### Q: Why is the Windows bundle so large?

**A**: PyInstaller includes the Python interpreter and all dependencies. This is normal and ensures the application works without requiring Python to be installed.

### Q: Can I bundle for Raspberry Pi?

**A**: The Unix distribution package works on Raspberry Pi. Simply copy the `dist/media-player-unix` folder to your Pi and follow the included README.

### Q: Does the bundle include my configuration?

**A**: No, `config.json` is excluded from bundles (it's in .gitignore). Users will create their own configuration through the web interface.

## See Also

- [Main README](../README.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Raspberry Pi Setup](RASPBERRY_PI_SETUP.md)
- [PyInstaller Documentation](https://pyinstaller.org/)
