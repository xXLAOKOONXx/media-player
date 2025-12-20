# Custom Track Start and End Times - Implementation Summary

## Overview

This document provides a comprehensive summary of the custom track start and end times feature implementation for the media player.

## Feature Description

The feature allows users to specify custom start and end times for each track in a playlist. When a track is played:
- Playback begins at the specified start time (instead of 0:00)
- Playback stops at the specified end time (instead of the track's natural end)

This is useful for:
- Skipping intros or outros
- Creating custom edits of songs
- Playing specific sections of long recordings
- Creating seamless mixes with precise timing

## Implementation Components

### 1. Backend (Python/Flask)

#### PlaybackController (`backend/playback_controller.py`)

**ID3 Tag Support (Primary Method):**
- Reads custom ID3 tags from audio files: `LAO:MUSIC_START` and `LAO:MUSIC_END`
- Times are stored in milliseconds in the ID3 tags, converted to seconds internally
- Uses mutagen library to read TXXX (user-defined text) frames
- ID3 tags take precedence over M3U directives

**M3U Playlist Parsing (Fallback Method):**
- Recognizes VLC-style `#EXTVLCOPT` directives in M3U files as fallback
- Extracts `start-time=X.X` and `stop-time=X.X` values (in seconds)
- Used when ID3 tags are not present or file cannot be read
- Stores as `start_time` and `end_time` in track dictionary

**Playback Control:**
- Added state tracking: `track_start_time`, `track_custom_start`, `track_custom_end`, `pause_time`, `total_pause_duration`
- `play()` method: Uses pygame's `start=` parameter to seek to custom start time
- Monitoring thread: Checks elapsed time every 100ms and stops at custom end time
- Pause/resume: Properly tracks time spent paused to maintain accurate position

**New Methods:**
- `_read_id3_times(file_path)` - Read start/end times from ID3 tags
- `set_track_times(track_index, start_time, end_time)` - Set custom times for a track
- `get_playlist_tracks()` - Get all tracks with their custom times

#### Flask API (`backend/app.py`)

**New Endpoints:**
- `GET /api/playback/tracks` - Returns all tracks with custom times
- `PUT /api/playback/tracks/<track_index>/times` - Set/clear custom times

**Validation:**
- Start time must be non-negative
- End time must be non-negative
- Start time must be less than end time
- Track index must be valid

### 2. Frontend (React/TypeScript)

#### TrackTimesEditor Component

**Features:**
- Lists all tracks in the current playlist
- Shows custom times with visual indicator (📌)
- Edit mode with separate inputs for start/end times
- Supports MM:SS format (e.g., "1:30") or seconds (e.g., "90")
- Save/Cancel buttons with validation
- Clear button to remove custom times
- Error messages for invalid input
- Auto-refresh every 10 seconds (when tab visible)

**User Experience:**
- Intuitive time formatting
- Real-time validation feedback
- Clear visual distinction between tracks with/without custom times
- Responsive layout

#### NowPlaying Component Update

- Displays custom range when set: "Custom Range: 0:30 - 2:00"
- Formats times as MM:SS for readability
- Shows alongside track duration

#### App.tsx Update

- Added "Track Times" tab to main navigation
- Tab positioned between "Player" and "Library"

## Technical Details

### Time Tracking Algorithm

```python
# When playback starts
track_start_time = current_system_time
total_pause_duration = 0

# During monitoring (every 100ms)
if custom_end_time is set:
    elapsed = current_system_time - track_start_time - total_pause_duration
    effective_position = custom_start_time + elapsed
    if effective_position >= custom_end_time:
        advance_to_next_track()

# When paused
pause_time = current_system_time

# When resumed
total_pause_duration += current_system_time - pause_time
```

### Data Structure

```python
track = {
    'title': 'Song Title',
    'path': '/path/to/file.mp3',
    'duration': '180',  # seconds
    'start_time': 10.0,  # optional, in seconds (converted from ID3 milliseconds or M3U seconds)
    'end_time': 120.0    # optional, in seconds (converted from ID3 milliseconds or M3U seconds)
}
```

### ID3 Tag Format

Custom start and end times are stored in ID3v2 TXXX (user-defined text) frames:

```python
# ID3 tags (using mutagen)
from mutagen.id3 import TXXX

# Start time in milliseconds
audio.tags.add(TXXX(encoding=3, desc='LAO:MUSIC_START', text='10000'))  # 10 seconds

# End time in milliseconds  
audio.tags.add(TXXX(encoding=3, desc='LAO:MUSIC_END', text='120000'))  # 120 seconds
```

**Field Names:**
- `LAO:MUSIC_START` - Start time in milliseconds
- `LAO:MUSIC_END` - End time in milliseconds (also referred to as `LAO:MUSIC_END`)

**Priority:**
1. ID3 tags (if present and file exists)
2. M3U `#EXTVLCOPT` directives (fallback)

### M3U Format

```m3u
#EXTM3U
#EXTINF:180,Artist - Title
#EXTVLCOPT:start-time=10.0
#EXTVLCOPT:stop-time=120.0
/path/to/file.mp3
```

## Testing

### Unit Tests
- Playlist parsing with custom times ✅
- Track times API methods ✅
- Status API with custom times ✅
- ID3 tag reading ✅
- M3U fallback when ID3 not present ✅

### API Tests
- GET /api/playback/tracks ✅
- PUT /api/playback/tracks/<index>/times ✅
- Validation (negative, start >= end) ✅

### Manual Testing
- UI interaction (edit, save, cancel, clear) ✅
- Time format parsing (MM:SS, seconds) ✅
- Visual display in Player and Track Times tabs ✅
- Frontend build and TypeScript compilation ✅
- ID3 tag reading from real MP3 files ✅

### Security
- CodeQL scan: 0 vulnerabilities ✅

## Usage Examples

### Via ID3 Tags (Recommended)

Use the provided `id3_tag_manager.py` tool to add custom times to your MP3 files:

```bash
# Add ID3 tags to an existing MP3 file
python3 examples/id3_tag_manager.py add my_track.mp3 --start 10000 --end 120000

# Read ID3 tags from a file
python3 examples/id3_tag_manager.py read my_track.mp3

# Create a test MP3 with ID3 tags
python3 examples/id3_tag_manager.py create test.mp3 --start 5000 --end 60000
```

**Note:** Times are in milliseconds for ID3 tags.

### Via M3U Playlist (Fallback)

```m3u
#EXTM3U
#EXTINF:180,Example Song
#EXTVLCOPT:start-time=30.0
#EXTVLCOPT:stop-time=150.0
/music/song.mp3
```

### Via API

```bash
# Set custom times
curl -X PUT http://localhost:5000/api/playback/tracks/0/times \
  -H "Content-Type: application/json" \
  -d '{"start_time": 30.0, "end_time": 150.0}'

# Get all tracks
curl http://localhost:5000/api/playback/tracks

# Clear custom times
curl -X PUT http://localhost:5000/api/playback/tracks/0/times \
  -H "Content-Type: application/json" \
  -d '{"start_time": null, "end_time": null}'
```

### Via UI

1. Load a playlist in the Library tab
2. Navigate to the "Track Times" tab
3. Click "Edit" on any track
4. Enter start time (e.g., "0:30" or "30")
5. Enter end time (e.g., "2:30" or "150")
6. Click "Save"
7. Play the track to hear the custom range

## Limitations and Future Enhancements

### Current Limitations
- Custom times are session-only (not saved back to M3U files)
- Cannot edit times while a track is playing (must stop/pause first)
- Times are specified in seconds (no millisecond precision)

### Potential Enhancements
- Save custom times back to M3U files
- Visual waveform display with start/end markers
- Fade in/out at custom boundaries
- Keyboard shortcuts for quick time adjustments
- Copy/paste times between tracks
- Undo/redo support
- Batch editing for multiple tracks

## Files Modified

### Backend
- `backend/playback_controller.py` (155 lines added/modified)
- `backend/app.py` (39 lines added)

### Frontend
- `frontend/src/App.tsx` (20 lines added/modified)
- `frontend/src/components/NowPlaying.tsx` (23 lines added/modified)
- `frontend/src/components/TrackTimesEditor.tsx` (248 lines, new file)
- `frontend/src/components/TrackTimesEditor.css` (120 lines, new file)

### Examples/Tests
- `examples/example_playlist_with_times.m3u` (new file)
- `examples/test_track_times.py` (new file)
- `examples/test_api.py` (new file)

## Integration with Existing Features

### Crossfade
- Custom times work alongside crossfade functionality
- Crossfade calculations still use track duration
- End time is checked before crossfade logic

### Pause/Resume
- Pause tracking properly accounts for custom start times
- Resume continues from the correct position
- Total pause duration is tracked separately

### Playlist Navigation
- Next/previous track commands reset custom times for new track
- Track index is maintained correctly

### Volume Control
- No interaction with volume settings
- Custom times are independent of audio settings

## Conclusion

This implementation provides a robust, user-friendly feature for managing custom track start and end times. The code is well-structured, properly validated, and integrates seamlessly with existing functionality. All tests pass, and the security scan shows no vulnerabilities.
