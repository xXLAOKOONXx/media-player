# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Media Player application
This file configures how PyInstaller bundles the application
"""

import os
import sys

block_cipher = None

# Get the directory where this spec file is located
spec_root = os.path.abspath(SPECPATH)

# Define paths
static_folder = os.path.join(spec_root, 'static')

# Collect all files from the static folder (built frontend)
static_files = []
if os.path.exists(static_folder):
    for root, dirs, files in os.walk(static_folder):
        for file in files:
            file_path = os.path.join(root, file)
            # Calculate relative destination path from spec_root
            dest_dir = os.path.relpath(root, spec_root)
            static_files.append((file_path, dest_dir))

a = Analysis(
    ['app.py'],
    pathex=[spec_root],
    binaries=[],
    datas=[
        # Include all static files (built frontend)
        *static_files,
    ],
    hiddenimports=[
        'flask',
        'flask.json',
        'flask.json.provider',
        'flask_cors',
        'pygame',
        'mutagen',
        'werkzeug',
        'werkzeug.security',
        'werkzeug.utils',
        'jinja2',
        'jinja2.ext',
        'markupsafe',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    exclude_binaries=False,
    name='media-player',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Set to False for GUI-only mode (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
