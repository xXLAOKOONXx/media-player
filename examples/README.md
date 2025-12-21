# Example Configuration

This directory contains example files and legacy test scripts for the media player.

## Main Files

- `example_playlist.m3u` - Sample M3U playlist format
- `example_playlist_with_times.m3u` - Sample M3U playlist with custom start/end times
- `test_id3_playlist.m3u` - Playlist for ID3 tag testing
- `config.example.json` - Example configuration file with all settings
- `id3_tag_manager.py` - Utility script for managing ID3 tags in audio files
- `monitor_performance.py` - Performance monitoring utility
- `mediaplayer.service` - Systemd service file for auto-start
- `nginx-site.conf` - Nginx configuration for reverse proxy

## Test Audio Files

Test audio files are now located in `example_tracks/` directory:
- See `example_tracks/README.md` for details

## Legacy Test Scripts

The following test scripts are kept for reference but have been superseded by the new pytest-based test suite in `backend/tests/`:

- `test_api.py` - API endpoint tests → Use `backend/tests/test_api.py`
- `test_crossfade.py` - Crossfade functionality tests → Use `backend/tests/test_crossfade.py`
- `test_id3_support.py` - ID3 tag support tests (reference only)
- `test_music_tab.py` - Music manager tests → Use `backend/tests/test_music.py`
- `test_shuffle_first_track.py` - Shuffle mode tests (reference only)
- `test_track_times.py` - Track timing tests (reference only)

**To run the new test suite:**
```bash
# Unix/Linux/macOS
./run_tests.sh

# Windows
run_tests.bat

# Or directly with pytest
cd backend
pytest tests/
```

See `docs/TESTING.md` for comprehensive testing documentation.

## Configuration Sections

### Network Storages

Configure your network-attached storage (NAS) devices:

```json
{
  "network_storages": [
    {
      "id": 1,
      "name": "NAS Music Library",
      "type": "smb",
      "host": "192.168.1.10",
      "share": "music",
      "username": "mediauser",
      "password": "your_password_here",
      "mount_point": "/mnt/media_1"
    }
  ]
}
```

### Libraries

Define music libraries pointing to playlist folders:

```json
{
  "libraries": [
    {
      "id": 1,
      "name": "Main Playlists",
      "type": "playlist",
      "path": "/mnt/media_1/playlists",
      "storage_id": 1
    }
  ]
}
```

### Crossfading

Configure automatic crossfading between tracks:

```json
{
  "crossfade": {
    "enabled": true,
    "duration_ms": 3000,
    "fade_out_start_before_end_ms": 5000
  }
}
```

**Parameters:**
- `enabled` (boolean): Enable/disable crossfading
- `duration_ms` (number): Fade duration in milliseconds (default: 3000)
- `fade_out_start_before_end_ms` (number): When to start fading before track ends (default: 5000)

See [docs/CROSSFADING.md](../docs/CROSSFADING.md) for detailed information.

## Usage

### Creating a Playlist

M3U playlists are simple text files with the extension `.m3u` or `.m3u8`. Here's the format:

```
#EXTM3U
#EXTINF:180,Artist Name - Song Title
/path/to/song1.mp3
#EXTINF:240,Another Artist - Another Song
/path/to/song2.mp3
```

- `#EXTM3U` - Header indicating extended M3U format
- `#EXTINF:duration,title` - Track metadata (duration in seconds)
- File path - Absolute or relative path to the audio file

### Supported Audio Formats

The media player supports the following audio formats through pygame:
- MP3
- WAV
- OGG Vorbis
- FLAC
- AAC (with proper codecs installed)

### Configuration

The application stores its configuration in `backend/config.json`. You can manage this through the web UI, or edit it manually following the example format.

## Tips

1. **Organize Your Music**
   - Keep playlists in a dedicated folder
   - Use meaningful names for playlists
   - Keep audio files organized by artist/album

2. **Network Paths**
   - For network storage, mount the share first
   - Use the mount point in your playlist paths
   - Example: `/mnt/media_1/music/song.mp3`

3. **Relative Paths**
   - Paths in playlists can be relative to the playlist location
   - Example: If playlist is in `/music/playlists/rock.m3u`
   - Track path can be `../albums/rock/track.mp3`

4. **Testing**
   - Test playlists with a small number of tracks first
   - Verify all paths are correct
   - Check that files are readable by the user running the service