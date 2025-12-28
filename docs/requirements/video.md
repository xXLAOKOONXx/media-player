# Video View Requirements

URL: `/video`

Source component:
- `frontend/src/pages/VideoPage.tsx`

## Purpose

The Video view provides video playback functionality with library management, playlist support, and playback controls.

## Layout

The Video page uses a tabbed interface with three main sections:

### Navigation Tabs

- **Player** - Video player with playback controls
- **Playlists** - Video playlist management
- **Library** - Video library and collection management

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

Video playback is handled client-side in the browser using HTML5 video elements. The backend provides:

### Backend Components

1. **VideoPlaybackController** (`backend/video_playback_controller.py`)
   - Manages playlist state
   - Tracks playback status
   - Handles shuffle and repeat modes
   - Maintains volume settings

2. **VideoManager** (`backend/video_manager.py`)
   - Scans video library folders
   - Creates M3U playlists
   - Filters and searches videos

3. **API Endpoints** (in `backend/app.py`)
   - `/api/video/libraries/*` - Library management
   - `/api/video/playlists/*` - Playlist management
   - `/api/video/playback/*` - Playback control

### Supported Video Formats

The following video formats are supported (via HTML5 video):
- MP4 (.mp4, .m4v)
- WebM (.webm)
- MKV (.mkv)
- AVI (.avi)
- MOV (.mov)
- WMV (.wmv)
- FLV (.flv)
- MPEG (.mpg, .mpeg)

Note: Actual playback support depends on browser codec support.

## Configuration

### Server-side Configuration

Video playback requires no special server configuration as videos are streamed directly to the browser using standard HTTP file serving.

For optimal performance:
1. Ensure video files are stored on fast storage (local disk or high-speed network storage)
2. Use commonly supported codecs (H.264/AAC for MP4) for best browser compatibility
3. Consider transcoding videos to web-friendly formats if playback issues occur

### Client-side Requirements

- Modern web browser with HTML5 video support
- Sufficient bandwidth for video streaming
- Recommended: Hardware video decoding support for 1080p+ content

## Default Routes

- `/video` redirects to `/video/player`
- All video routes are under the `/video/*` path structure
