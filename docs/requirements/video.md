# Video View Requirements

URL: `/video`

Source component:
- `frontend/src/pages/VideoPage.tsx`

## Purpose

The Video view provides video playback functionality with library management, playlist support, and playback controls.

## Layout

The Video page uses a tabbed interface with four main sections:

### Navigation Tabs

- **Player** - Video player with playback controls
- **Playlists** - Video playlist management
- **Library** - Video library and collection management
- **Settings** - Application settings (shared with Audio view)

## Sub-views

### Player Tab (URL: `/video/player`)

See [video-player.md](video-player.md) for detailed requirements.

Features:
- Currently playing video display
- Playback progress and seeking
- Transport controls (play/pause/stop/next/previous)
- Mode controls (shuffle/repeat)
- Volume controls
- "Up Next" preview

### Playlists Tab (URL: `/video/playlists`)

Features:
- Manage video playlist folders
- Browse available `.m3u` playlists
- Start playback from playlists
- Rename/delete playlist folders

Similar to audio playlist management, adapted for videos.

### Library Tab (URL: `/video/library`)

See [video-library.md](video-library.md) for detailed requirements.

Features:
- Manage video library folders
- Scan for videos in configured folders
- Search and filter videos
- Select videos and create playlists
- Add videos to current playback queue

## Video Playback Implementation

Video playback uses **server-side rendering with MPV player** (similar to audio with pygame), providing HDMI output for Raspberry Pi setups. Falls back to client-side browser playback if MPV is unavailable.

### Backend Components

1. **VideoPlaybackController** (`backend/video_playback_controller.py`)
   - **Server-side video playback** using MPV player
   - Opens videos in **fullscreen by default**
   - **Auto-starts playback** when videos are added to playlist
   - **Extracts video duration** using mutagen (for MP4) or MPV fallback for timeline display
   - Manages playlist state and navigation
   - Tracks playback status and position
   - Handles shuffle and repeat modes
   - Controls volume and seeking
   - Auto-plays next video on completion
   - Falls back to state-only mode if MPV unavailable

2. **VideoManager** (`backend/video_manager.py`)
   - Scans video library folders
   - Creates M3U playlists
   - Filters and searches videos
   - **SQLite caching** for faster library loading

3. **VideoCache** (`backend/video_cache.py`)
   - SQLite database for video metadata caching
   - Stores file paths, titles, sizes, and durations
   - Dramatically improves library loading performance
   - Automatic cache invalidation on folder changes

4. **API Endpoints** (in `backend/app.py`)
   - `/api/video/libraries/*` - Library management
   - `/api/video/playlists/*` - Playlist management
   - `/api/video/playback/*` - Playback control
   - `/api/video/thumbnail/by-id/<media_id>` - Returns cached thumbnail image data

### Supported Video Formats

MPV supports a wide range of video formats with hardware acceleration:
- MP4 (.mp4, .m4v) - Best compatibility
- MKV (.mkv) - High quality container
- AVI (.avi)
- MOV (.mov)
- WebM (.webm)
- WMV (.wmv)
- FLV (.flv)
- MPEG (.mpg, .mpeg)
- And many more formats supported by MPV/ffmpeg

## Configuration

### Server-side Video Playback Setup

> **⚠️ Important:** The **libmpv** library must be installed and available on the server for video playback to work. This is the shared library that python-mpv bindings use to interface with MPV.

**Required Software:**

1. **MPV Media Player and libmpv library**
   ```bash
   # Raspberry Pi / Debian / Ubuntu
   sudo apt install mpv libmpv2
   
   # macOS
   brew install mpv
   
   # Fedora / RedHat
   sudo dnf install mpv mpv-libs
   ```

2. **Python MPV Bindings**
   ```bash
   cd backend
   pip install python-mpv
   # Or with uv:
   uv pip install python-mpv
   ```

**Hardware Requirements:**
- Display connected via HDMI or other video output
- Audio output (HDMI audio or separate audio device)
- For Raspberry Pi: GPU memory allocation of at least 128MB recommended

**Features:**
- Videos play on server's display (HDMI to TV/monitor)
- Hardware-accelerated decoding (critical for Raspberry Pi performance)
- Full volume and seek control
- Automatic playlist navigation
- Respects repeat (off/all/one) and shuffle modes

**Raspberry Pi Optimization:**
- MPV automatically uses hardware video decoding on Raspberry Pi
- Works with H.264/H.265 hardware acceleration
- Configure GPU memory in `/boot/config.txt`: `gpu_mem=256`

**Fallback Mode:**
If python-mpv is not installed:
- System operates in state-only mode
- Playlist and library management still functional
- Videos can be played client-side via browser
- No server display output

### Storage Configuration

For optimal performance:
1. Store videos on fast storage (local disk or high-speed network storage)
2. Use commonly supported codecs (H.264/AAC in MP4 container)
3. Ensure proper file permissions for backend access
4. For network storage, ensure sufficient bandwidth

### Client-side Requirements (Fallback Mode Only)

If MPV is not available, videos can play in the browser:
- Modern web browser with HTML5 video support
- Sufficient network bandwidth for streaming
- Hardware video decoding recommended for HD content

### Settings Tab (URL: `/video/settings`)

See [settings.md](settings.md) for detailed requirements.

Features:
- Configure audio crossfade settings
- Configure video playback settings (fullscreen mode, preferred screen)
- Shared settings view accessible from both Audio and Video sections

## Default Routes

- `/video` redirects to `/video/player`
- All video routes are under the `/video/*` path structure
