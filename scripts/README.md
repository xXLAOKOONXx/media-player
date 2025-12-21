# Scripts

This directory contains utility scripts for the media player project.

## Available Scripts

### `generate_screenshots.py`

Generates UI screenshots for documentation using Playwright automation.

**Requirements:**
```bash
pip install playwright requests
playwright install chromium
```

**Usage:**
```bash
# Make sure the server is running first
cd backend
python app.py

# In another terminal, generate screenshots
python scripts/generate_screenshots.py

# Custom output directory
python scripts/generate_screenshots.py --output docs/images

# Custom server URL
python scripts/generate_screenshots.py --url http://localhost:3000

# Skip server check (if you know it's running)
python scripts/generate_screenshots.py --no-wait
```

**Output:**
- Screenshots are saved to `docs/screenshots/` by default
- A `SCREENSHOTS.md` file is generated with documentation
- Screenshots are numbered and named by UI section

**Generated Screenshots:**
1. `00_overview.png` - Full page overview
2. `01_player_tab.png` - Main player interface
3. `02_storage_tab.png` - Storage management
4. `03_playlists_tab.png` - Playlists management
5. `04_sound_effects_tab.png` - Sound effects
6. `05_music_tab.png` - Music management

## Adding New Scripts

When adding new utility scripts to this directory:
1. Add appropriate shebang line (e.g., `#!/usr/bin/env python3`)
2. Make the script executable: `chmod +x script_name.py`
3. Add documentation to this README
4. Include a help message in the script (`--help`)
