# Music Tab Feature - Usage Guide

## Overview

The Music Tab feature allows you to manage music libraries, search and filter tracks by metadata, and create M3U playlists.

## Getting Started

### 1. Configure Playlist Folder

Before creating playlists, configure where they should be saved:

1. Click the "Music" tab
2. Click "Configure Playlist Folder"
3. Browse to select a folder or type the path
4. Click "Save"

### 2. Add Music Folders

Add folders containing your music files:

1. Click "Add Music Folder"
2. Enter a name (e.g., "Rock Music")
3. Browse to select the folder path
4. Check "Scan subfolders recursively" if you want to include subdirectories
5. Click "Add Folder"

The system will scan for supported audio files:
- MP3, WAV, OGG, FLAC, M4A, AAC, WMA, OPUS

### 3. View Tracks with Metadata

Select a music folder to view all tracks with metadata extracted from ID3 tags:
- **Title**: Song title
- **Artist**: Artist name
- **Album**: Album name
- **Duration**: Track length in minutes:seconds
- **Tags**: Custom tags from ID3 "LAO:TAGS" field

### 4. Search and Filter

Use the search filters to find specific tracks:

- **Artist**: Search by artist name (case-insensitive)
- **Title**: Search by song title (case-insensitive)
- **Tags**: Comma-separated list of tags to match
- **Min Duration**: Minimum track length in seconds
- **Max Duration**: Maximum track length in seconds

All filters can be combined for precise searches.

### 5. Create Playlists

Create a new playlist from selected tracks:

1. Check the boxes next to tracks you want to include
2. Click "Create Playlist" button (shows number of selected tracks)
3. Enter a playlist name
4. Click "Create Playlist"

The playlist is saved as an M3U file with:
- Relative paths (when possible) for portability
- EXTINF metadata (duration, artist, title)
- Standard M3U format compatible with most players

### 6. Add Tracks to Existing Playlists

Add individual tracks to existing playlists:

1. Click the playlist icon (➕) next to a track
2. Select an existing playlist from the dropdown
3. Click "Add to Playlist"

If the track already exists in the playlist, you'll be notified.

## ID3 Tags Support

### Standard Tags
- **TPE1**: Artist
- **TIT2**: Title
- **TALB**: Album
- **Duration**: Automatically extracted from audio file

### Custom Tags
The system reads a custom ID3 field called "LAO:TAGS" which should contain a stringified JSON array of tags:

```
LAO:TAGS = "['rock', 'classic', 'energetic']"
```

or simple comma-separated:

```
LAO:TAGS = "rock,classic,energetic"
```

You can set this field using ID3 tag editors like:
- Mp3tag
- Kid3
- MusicBrainz Picard
- Or programmatically with mutagen

## M3U Playlist Format

Created playlists follow the extended M3U format:

```m3u
#EXTM3U
#EXTINF:180,Artist Name - Song Title
relative/path/to/song.mp3
#EXTINF:240,Another Artist - Another Song
relative/path/to/another.mp3
```

Relative paths make playlists portable between systems when the music and playlist folders maintain the same relative structure.

## Tips

1. **Recursive Scanning**: Use recursive mode for folders with nested subdirectories organized by artist/album
2. **Non-Recursive**: Use non-recursive mode for flat folder structures or when you want to keep subfolders separate
3. **Tags**: Use consistent tag names across your library for better filtering
4. **Playlist Organization**: Configure a dedicated playlist folder to keep all playlists in one location
5. **Search Performance**: Filter by artist or title first to narrow down results before applying other filters

## Troubleshooting

### No tracks appear
- Verify the folder path exists and contains audio files
- Check that files have supported extensions (.mp3, .wav, etc.)
- Try recursive mode if files are in subdirectories

### Tags not showing
- Ensure ID3 tags are present in your audio files
- Use an ID3 tag editor to verify "LAO:TAGS" field exists
- Tags field format should be a stringified list or comma-separated

### Playlist creation fails
- Configure the playlist folder first
- Ensure you have write permissions to the playlist folder
- Check that playlist name doesn't contain invalid characters

### Duplicate prevention not working
- Paths are normalized before comparison
- Ensure the same track path is being used
- Relative paths are compared after normalization

## Example Workflow

1. Add music folder: `/music/library` (recursive)
2. Configure playlist folder: `/music/playlists`
3. Search: artist="Beatles", tags="rock"
4. Select 10 tracks
5. Create playlist: "Beatles Rock Collection"
6. Result: `/music/playlists/Beatles Rock Collection.m3u`

The playlist will contain relative paths like:
```
../../library/Beatles/Abbey Road/01 - Come Together.mp3
```

## API Endpoints

If you're integrating programmatically:

- `GET /api/music` - List music folders
- `POST /api/music` - Add music folder
- `GET /api/music/:id/tracks` - Get tracks with metadata
- `POST /api/music/search` - Search tracks
- `POST /api/music/playlists/create` - Create playlist
- `POST /api/music/playlists/:name/add-track` - Add track to playlist
- `GET/PUT /api/music/playlists-folder` - Manage playlist folder config

See the backend API documentation for full details.
