# Media Player

A comprehensive media player system designed for Raspberry Pi with network storage support, web-based control interface, and playlist management.

## 🎯 Features

### Audio Features
- **Network Storage Management**: Configure SMB/CIFS and NFS network storage locations
- **Playlist Management**: Organize your media files into playlist folders
- **Playlist Support**: Play M3U and M3U8 playlist files
- **Sound Effects**: Play sound effects in parallel with music
  - Configure sound effects folders containing audio files
  - Support for MP3, WAV, OGG, FLAC, M4A, and AAC formats
  - Click-to-play interface for instant sound effect playback
  - Plays simultaneously alongside music tracks
- **Advanced Playback Controls**: 
  - Play, pause, stop, skip tracks, and adjust volume
  - Shuffle mode for randomized playback
  - Repeat modes (off, all tracks, single track)
  - Progress bar with seek functionality
  - Track time display (current position / total duration)
  - **Proper crossfade with overlap**: Simultaneous fade-out/fade-in between tracks
  - Visual crossfade indicators
- **Smart Duration Detection**: Automatically extracts accurate track duration from audio files using mutagen
- **Real-Time Status**: See what's currently playing in real-time
- **Performance Monitoring**: Comprehensive logging for monitoring playback performance

### Video Features
- **Video Library Management**: Organize and scan video folders
  - Support for MP4, MKV, AVI, MOV, WebM, and more
  - Recursive folder scanning
  - Search and filter videos
- **Video Playlist Support**: Create and manage M3U video playlists
  - Add videos to playlists
  - Play playlists with shuffle and repeat modes
- **Video Playback Controls**:
  - Browser-based HTML5 video playback
  - Full transport controls (play/pause/stop/next/previous)
  - Seek to any position
  - Volume control
  - Playlist navigation
- **Client-Side Video Rendering**: Videos play directly in the browser using HTML5 video elements

### General Features
- **Web-Based Control**: Modern React-based UI accessible from any device on your network
- **Raspberry Pi Optimized**: Designed to run on Raspberry Pi with HDMI audio output

## 📋 Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Raspberry Pi Setup](#raspberry-pi-setup)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

## 🏗️ Architecture

```mermaid
graph TB
    A[Web Browser] -->|HTTP| B[React Frontend]
    B -->|REST API| C[Flask Backend]
    C -->|Controls| D[Pygame Audio]
    C -->|Manages| E[Network Storage]
    C -->|Reads| F[M3U Playlists]
    D -->|HDMI Audio| G[Audio Receiver]
    E -->|Mounts| H[SMB/NFS Shares]
    F -->|Located in| E
    
    style A fill:#667eea
    style B fill:#764ba2
    style C fill:#f093fb
    style D fill:#4facfe
    style G fill:#43e97b
```

### Component Overview

```mermaid
graph LR
    subgraph Frontend
        A[App.tsx] --> B[StorageManager]
        A --> C[PlaylistManager]
        A --> D[PlaybackControls]
        A --> E[NowPlaying]
    end
    
    subgraph Backend
        F[app.py] --> G[StorageManager]
        F --> H[LibraryManager]
        F --> I[PlaybackController]
    end
    
    B -.API.-> F
    C -.API.-> F
    D -.API.-> F
    E -.API.-> F
    
    style A fill:#667eea
    style F fill:#764ba2
```

## 📦 Prerequisites

### For Development and Testing

- Python 3.8 or higher
- Node.js 14 or higher
- npm or yarn

### For Raspberry Pi Deployment

- Raspberry Pi (3 or newer recommended)
- Raspberry Pi OS (formerly Raspbian)
- HDMI cable connected to audio receiver
- Network connection (WiFi or Ethernet)

## 🚀 Installation

### Quick Start (Development)

1. **Clone the repository**
   ```bash
   git clone https://github.com/xXLAOKOONXx/media-player.git
   cd media-player
   ```

2. **Install backend dependencies**
   
   **Quick Start (Recommended):**
   ```bash
   # Use the automated setup script (installs all dependencies)
   ./start-dev.sh
   ```
   
   **Manual Installation with uv (recommended - 10x faster):**
   ```bash
   cd backend
   # Install uv if not already installed
   pip install uv
   
   # Install dependencies from uv.lock
   uv sync --no-build-isolation
   ```
   
   See [UV Setup Guide](docs/UV_SETUP.md) for more details.

3. **Build and start the application**
   ```bash
   # If you used start-dev.sh, it already built the frontend
   # Otherwise, build frontend manually:
   cd frontend
   npm install
   npm run build
   
   # Start backend (serves both API and frontend)
   cd ../backend
   uv run python app.py
   ```
   
   The application will run on `http://localhost:5000`

4. **Access the application**
   Open your web browser and navigate to `http://localhost:5000`

### Development Mode (Frontend Hot Reload)

For frontend development with hot reload:

```bash
# Terminal 1 - Backend API
cd backend
uv run python app.py

# Terminal 2 - Frontend dev server with proxy
cd frontend
npm run dev
```

Then access the frontend at `http://localhost:5173` (Vite's default port)

### Production Build

1. **Build the frontend**
   ```bash
   cd frontend
   npm run build
   ```

2. **Serve the frontend through Flask** (optional)
   You can configure Flask to serve the built React app, or use a reverse proxy like nginx.

### Creating Distributable Bundles

For creating shippable bundles with the built frontend:

**Automated (GitHub Actions - Recommended for Windows):**
- Go to the Actions tab in GitHub
- Run the "Build Windows Executable" workflow
- Download the artifact when complete

**Local Build:**

**Windows** (creates standalone executable):
```bash
build.bat
```

**Unix/Linux/macOS** (creates distribution package):
```bash
./build.sh
```

See the [Bundling Guide](docs/BUNDLING.md) for detailed instructions on creating and distributing bundles.

## 🔧 Configuration

### Backend Configuration

The backend stores configuration in `config.json` in the backend directory. This file is automatically created and managed through the web interface.

Example `config.json`:
```json
{
  "network_storages": [
    {
      "id": 1,
      "name": "NAS Music",
      "type": "smb",
      "host": "192.168.1.100",
      "share": "music",
      "username": "user",
      "password": "password",
      "mount_point": "/mnt/media_1"
    }
  ],
  "playlists": [
    {
      "id": 1,
      "name": "My Playlists",
      "type": "playlist",
      "path": "/mnt/media_1/playlists",
      "storage_id": 1
    }
  ]
}
```

### Frontend Configuration

Create a `.env` file in the `frontend` directory:

```env
REACT_APP_API_URL=http://localhost:5000
```

For production on Raspberry Pi:
```env
REACT_APP_API_URL=http://raspberrypi.local:5000
```

## 📖 Usage

### 1. Configure Network Storage

1. Navigate to the **Storage** tab
2. Click **+ Add Storage**
3. Fill in the storage details:
   - Storage Name: A friendly name for your storage
   - Type: SMB/CIFS or NFS
   - Host/Server: IP address or hostname
   - Share Name: The network share name
   - Username/Password: Credentials for accessing the share
4. Click **Add Storage**

### 2. Add Playlist Folders

1. Navigate to the **Playlists** tab
2. Click **+ Add Playlist Folder**
3. Enter a folder name and path to your playlist folder
4. Use the **Browse** button to navigate your filesystem
5. Click **Add Playlist Folder**
6. Use the ✏️ button to rename or 🗑️ button to delete a playlist folder

### 3. Play Music

1. In the **Playlists** tab, select a playlist folder
2. Browse the available playlists
3. Click **Play** on any playlist to start playback
4. Navigate to the **Player** tab to control playback

### 4. Control Playback

In the **Player** tab, you can:
- **Shuffle** (🔀): Toggle shuffle mode to randomize track playback order
- **Repeat** (↻/🔁/🔂): Cycle through repeat modes:
  - ↻ Off: Play playlist once and stop
  - 🔁 All: Repeat entire playlist
  - 🔂 One: Repeat current track
- **Play/Pause**: Start or pause playback
- **Stop**: Stop playback completely
- **Previous/Next**: Navigate between tracks
- **Volume**: Adjust the playback volume
- **Progress Bar**: Click or drag to seek to any position in the current track
- **Track Time**: View current position and total duration (extracted automatically from audio files)
- **Crossfade Indicator**: Green gradient shows where track will fade out (last 5 seconds)
- **Crossfade**: Smooth transitions with real overlap between tracks
- **Now Playing**: See the current track information

### 5. Play Sound Effects

1. Navigate to the **Sound Effects** tab
2. Click **+ Add Sound Effects Folder**
3. Enter a folder name and path to your sound effects folder
4. Use the **Browse** button to navigate your filesystem
5. Click **Add Sound Effects Folder**
6. Select a sound effects folder to view available audio files
7. Click **Play** on any sound effect to play it alongside the currently playing music

Sound effects will play in parallel with music using separate audio channels, allowing you to trigger sound effects without interrupting music playback.

### 6. Video Playback

1. Navigate to the **Video** section in the main navigation
2. Go to the **Library** tab
3. Click **+ Add Video Library** to add a video folder
4. Enter a library name and path to your video folder
5. Use the **Browse** button to navigate your filesystem
6. Optionally enable "Scan subfolders recursively" for nested folder structures
7. Click **Add Library**
8. Select the library to view available videos
9. Select videos and create playlists, or add them to the current playback queue
10. Navigate to the **Player** tab to watch videos with full playback controls

#### Supported Video Formats

The video player supports the following formats (via HTML5 video):
- MP4 (.mp4, .m4v) - Best compatibility
- WebM (.webm)
- MKV (.mkv)
- AVI (.avi)
- MOV (.mov)
- WMV (.wmv)
- FLV (.flv)
- MPEG (.mpg, .mpeg)

**Note**: Actual playback support depends on your browser's codec support. For best compatibility, use H.264/AAC encoded MP4 files.

#### Video Playback Configuration

The media player supports **server-side video playback** using the MPV player, similar to how audio uses pygame. Videos play on the server's display output (HDMI/monitor), making it ideal for Raspberry Pi setups connected to TVs.

> **⚠️ Important:** The **libmpv** library must be installed and available on the server for video playback to work. This is the shared library that python-mpv bindings use to interface with MPV.

##### Server-side Playback Setup (Recommended for Raspberry Pi)

**Prerequisites:**
1. **Install MPV player and libmpv library**:
   ```bash
   # On Raspberry Pi / Debian / Ubuntu
   sudo apt install mpv libmpv2
   
   # On macOS
   brew install mpv
   
   # On Fedora / RedHat
   sudo dnf install mpv mpv-libs
   ```

2. **Install Python MPV bindings**:
   ```bash
   cd backend
   pip install python-mpv
   # Or if using uv:
   uv pip install python-mpv
   ```

**Features:**
- Videos play on the server's display output (HDMI to TV/monitor)
- Full hardware acceleration support (important for Raspberry Pi)
- Proper volume control
- Seek support
- Automatic next track on video end
- Respects repeat and shuffle modes

**Configuration:**
- No additional configuration needed after installing mpv
- Videos automatically play on the default display in **fullscreen mode**
- Videos **auto-start when added** to the current playlist
- Volume is controlled through the server's audio output
- Works seamlessly with HDMI audio/video output

**Fallback Mode:**
If python-mpv is not installed, the system falls back to state-only mode where:
- Playlist management still works
- API endpoints function normally
- Videos can only be played client-side in the browser
- No server-side video output

##### Client-side Playback Alternative

For systems without MPV or when remote viewing is needed:
- Videos are streamed to the browser via HTTP
- Browser's native HTML5 video player handles decoding
- Works on any device with a modern web browser
- Network bandwidth requirements apply

**Storage recommendations** (for both modes):
- Store videos on fast storage (local disk or high-speed network storage)
- Use commonly supported codecs (H.264/AAC in MP4 container)
- Ensure proper file permissions for the backend to access videos

### 7. Crossfade Configuration

The media player features intelligent crossfading with real overlap between tracks:

- **Automatic Duration Detection**: Track durations are extracted directly from audio files using mutagen, ensuring accurate timing
- **Configurable Crossfade**: 
  - Default crossfade duration: 3 seconds
  - Fade starts 5 seconds before track end
  - Both tracks play simultaneously during crossfade
- **Smart Fallback**: For large audio files that can't be loaded into memory, the system automatically falls back to queue-based crossfade
- **Performance Monitoring**: Comprehensive logging tracks crossfade performance and helps diagnose issues

## 🍓 Raspberry Pi Setup

### Hardware Setup

1. Connect Raspberry Pi to audio receiver via HDMI
2. Ensure network connectivity (WiFi or Ethernet)
3. Optional: Connect keyboard and monitor for initial setup

### Software Installation

1. **Install Raspberry Pi OS**
   ```bash
   # Update system
   sudo apt update
   sudo apt upgrade -y
   ```

2. **Install Python dependencies**
   ```bash
   sudo apt install -y python3 python3-pip python3-pygame
   cd ~/media-player/backend
   pip3 install -r requirements.txt
   ```

3. **Install Node.js** (for building frontend)
   ```bash
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt install -y nodejs
   ```

4. **Build frontend**
   ```bash
   cd ~/media-player/frontend
   npm install
   npm run build
   ```

5. **Configure audio output to HDMI**
   ```bash
   # Edit config.txt
   sudo nano /boot/config.txt
   
   # Add or uncomment:
   hdmi_drive=2
   
   # Set audio output
   sudo raspi-config
   # Navigate to: System Options -> Audio -> HDMI
   ```

6. **Install network storage support**
   ```bash
   # For SMB/CIFS
   sudo apt install -y cifs-utils
   
   # For NFS
   sudo apt install -y nfs-common
   ```

### Auto-Start on Boot

Create a systemd service:

1. **Create backend service**
   ```bash
   sudo nano /etc/systemd/system/mediaplayer.service
   ```

   ```ini
   [Unit]
   Description=Media Player Backend
   After=network.target

   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/home/pi/media-player/backend
   ExecStart=/usr/bin/python3 /home/pi/media-player/backend/app.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

2. **Enable and start service**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable mediaplayer.service
   sudo systemctl start mediaplayer.service
   ```

3. **Check status**
   ```bash
   sudo systemctl status mediaplayer.service
   ```

### Accessing the UI

Once running, access the web interface from any device on your network:
- `http://raspberrypi.local:3000` (if mDNS is enabled)
- `http://[RASPBERRY_PI_IP]:3000`

## 👨‍💻 Development

### Project Structure

```
media-player/
├── backend/                 # Python Flask backend
│   ├── app.py              # Main Flask application
│   ├── storage_manager.py  # Network storage handling
│   ├── library_manager.py  # Playlist and library management
│   ├── sound_effects_manager.py # Sound effects management
│   ├── playback_controller.py # Audio playback control
│   ├── requirements.txt    # Python dependencies
│   └── tests/              # Pytest test suite
│       ├── conftest.py     # Test fixtures
│       ├── test_api.py     # API endpoint tests
│       ├── test_crossfade.py # Crossfade tests
│       ├── test_music.py   # Music management tests
│       └── test_e2e.py     # End-to-end tests
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   │   ├── StorageManager.tsx
│   │   │   ├── PlaylistManager.tsx
│   │   │   ├── SoundEffectsManager.tsx
│   │   │   ├── PlaybackControls.tsx
│   │   │   └── NowPlaying.tsx
│   │   ├── App.tsx        # Main App component
│   │   └── index.tsx      # Entry point
│   └── package.json       # npm dependencies
├── docs/                   # Documentation
│   └── TESTING.md         # Testing guide
├── scripts/                # Utility scripts
│   └── generate_screenshots.py # UI screenshot generator
├── examples/
│   └── example_tracks/    # Test audio files
├── run_tests.sh           # Test runner (Unix/Linux/macOS)
└── run_tests.bat          # Test runner (Windows)
```

### Testing

The project includes a comprehensive test suite. See [docs/TESTING.md](docs/TESTING.md) for full details.

**Quick start:**
```bash
# Unix/Linux/macOS
./run_tests.sh

# Windows
run_tests.bat

# Or with pytest directly
cd backend
pytest tests/
```

**Test categories:**
- Unit tests: `test_crossfade.py`, `test_music.py`
- API tests: `test_api.py` (requires running server)
- End-to-end tests: `test_e2e.py` (requires running server)

### API Endpoints

#### Storage Management
- `GET /api/storage` - List all network storages
- `POST /api/storage` - Add new network storage
- `DELETE /api/storage/:id` - Delete network storage

#### Playlist Management
- `GET /api/playlists` - List all playlist folders
- `POST /api/playlists` - Add new playlist folder
- `PUT /api/playlists/:id` - Rename playlist folder
- `DELETE /api/playlists/:id` - Delete playlist folder
- `GET /api/playlists/:id/files` - Get playlists in folder

#### Sound Effects Management
- `GET /api/soundeffects` - List all sound effects folders
- `POST /api/soundeffects` - Add new sound effects folder
- `PUT /api/soundeffects/:id` - Rename sound effects folder
- `DELETE /api/soundeffects/:id` - Delete sound effects folder
- `GET /api/soundeffects/:id/files` - Get audio files in folder
- `POST /api/soundeffects/play` - Play a sound effect in parallel with music

#### Playback Control
- `POST /api/playback/play` - Start/resume playback
- `POST /api/playback/pause` - Pause playback
- `POST /api/playback/stop` - Stop playback
- `POST /api/playback/next` - Next track
- `POST /api/playback/previous` - Previous track
- `POST /api/playback/volume` - Set volume
- `POST /api/playback/shuffle` - Toggle shuffle mode
- `POST /api/playback/repeat` - Set repeat mode (none/all/one)
- `POST /api/playback/seek` - Seek to position in track
- `GET /api/playback/status` - Get playback status (includes shuffle, repeat, position)

#### File System
- `POST /api/browse` - Browse filesystem path

### Making Changes

1. For backend changes, modify files in `backend/` directory
2. For frontend changes, modify files in `frontend/src/`
3. Test changes locally before deploying to Raspberry Pi

## 🔍 Troubleshooting

### Audio Issues

**Problem**: No audio output
```bash
# Check audio devices
aplay -l

# Test audio
speaker-test -t wav -c 2

# Force HDMI audio
sudo raspi-config
# System Options -> Audio -> HDMI
```

**Problem**: Pygame mixer errors
```bash
# Reinstall pygame
pip3 uninstall pygame
pip3 install pygame
```

### Network Storage Issues

**Problem**: Cannot mount network share
```bash
# Test SMB connection
smbclient -L //server_ip -U username

# Manual mount test
sudo mount -t cifs //server/share /mnt/test -o username=user,password=pass

# Check mount points
mount | grep cifs
```

**Problem**: Permission denied on mounted share
```bash
# Mount with proper permissions
sudo mount -t cifs //server/share /mnt/test -o username=user,password=pass,uid=1000,gid=1000
```

### Backend Issues

**Problem**: Flask won't start
```bash
# Check if port 5000 is in use
sudo netstat -tlnp | grep 5000

# Check Python version
python3 --version

# Check dependencies
pip3 list
```

**Problem**: CORS errors in browser console
- Ensure Flask-CORS is installed: `pip3 install Flask-CORS`
- Check that CORS is enabled in `app.py`

### Frontend Issues

**Problem**: Cannot connect to backend
- Verify backend is running: `curl http://localhost:5000/api/playback/status`
- Check REACT_APP_API_URL in `.env` file
- Ensure no firewall blocking port 5000

**Problem**: Build fails
```bash
# Clear cache and rebuild
rm -rf node_modules package-lock.json
npm install
npm run build
```

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting a Pull Request.

**Important:** All new features must include responsive design for mobile devices. See the [Responsive Design Requirements](CONTRIBUTING.md#responsive-design-requirements) section in our contributing guidelines.

## 📧 Support

For issues and questions, please open an issue on the GitHub repository.