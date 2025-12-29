# Enhanced Video Metadata

The media player supports enhanced metadata caching for video files. This metadata can be extracted from:

1. **Video files directly** (MP4/M4V files with embedded metadata)
2. **NFO files** (XML files placed next to video files)

## Supported Metadata Fields

The following metadata fields are now cached for videos:

- **Title**: Video title
- **Artist**: Director, artist, or creator name
- **Tags/Genres**: List of genre tags or categories
- **Description**: Plot or content description
- **Premiere Date**: Release or premiere date
- **User Rating**: User score (0.0 to 10.0)
- **Thumbnail**: URL or path to poster/thumbnail image
- **Duration**: Video duration in seconds (extracted from video file)

## NFO File Format

NFO files should be placed next to video files with the same base name:
- Video: `movie.mp4`
- NFO: `movie.nfo`

### Example NFO File

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<movie>
    <title>Example Movie Title</title>
    <artist>Director Name</artist>
    <plot>This is the movie description.</plot>
    <premiered>2023-12-15</premiered>
    <userscore>8.5</userscore>
    <Genre>Action</Genre>
    <Genre>Sci-Fi</Genre>
    <thumb>https://example.com/poster.jpg</thumb>
</movie>
```

See `examples/example_video.nfo` for a complete example.

## NFO Field Mappings

The following NFO XML tags are recognized:

| NFO Tag | Metadata Field | Type | Description |
|---------|---------------|------|-------------|
| `title` | title | string | Video title |
| `artist` | artist | string | Director/artist name; if missing, uses `actor/name` values joined with `,` |
| `plot` | description | string | Plot or description |
| `premiered` | premiere_date | string | Release date (YYYY-MM-DD) |
| `userscore` | user_rating | float | User rating (0.0-10.0) |
| `Genre` or `genre` | tags | list | Genre tags (can have multiple) |
| `thumb` | thumbnail | string | Thumbnail URL or path |
| `start_time_in_ms` | start_time_in_ms | string | Custom start time in milliseconds |
| `end_time_in_ms` | end_time_in_ms | string | Custom end time in milliseconds |
| `lastplayed` | lastplayed | string | Last played date |

## Automatic Metadata Extraction

When you scan a video library:

1. The system first looks for metadata in the video file itself (for MP4/M4V files). Title may be read from `\xa9nam` and artists from `\xa9ART`.
2. Then it checks for an accompanying `.nfo` file
3. NFO metadata takes precedence over embedded metadata
4. All metadata is cached in the database for fast retrieval

## Caching Behavior

- Metadata is cached when you first add or scan a video library
- The cache is automatically used on subsequent requests
- Force a refresh by clicking the refresh button in the video library UI
- Cache is invalidated when library settings change (path, recursive setting)

## Example Usage

### Creating an NFO File for a Video

1. Create a video file: `vacation_2023.mp4`
2. Create an NFO file: `vacation_2023.nfo`
3. Add metadata to the NFO file:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<movie>
    <title>Summer Vacation 2023</title>
    <premiered>2023-08-15</premiered>
    <plot>Family vacation to the beach</plot>
    <Genre>Home Video</Genre>
    <userscore>10.0</userscore>
</movie>
```

4. Scan or refresh the video library
5. The metadata will be displayed in the video player UI

### Viewing Cached Metadata

The metadata is automatically included in:
- Video library listings (`/api/video/libraries/<id>/videos`)
- Video player current track information
- Search and filter operations

## Technical Details

### Database Schema

The video metadata is stored in the `videos` table with the following columns:

```sql
CREATE TABLE videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_id INTEGER NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    file_name TEXT NOT NULL,
    file_size INTEGER,
    title TEXT,
    duration REAL,
    last_modified REAL,
    cached_at REAL NOT NULL,
    tags TEXT,              -- JSON array
    artist TEXT,
    thumbnail TEXT,
    description TEXT,
    premiere_date TEXT,
    user_rating REAL,
    FOREIGN KEY (folder_id) REFERENCES video_folders (id) ON DELETE CASCADE
)
```

### Migration

Existing databases are automatically migrated to include the new metadata fields when the application starts. No manual intervention is required.

### API Response Format

Video objects returned by the API now include:

```json
{
  "path": "/path/to/video.mp4",
  "name": "video.mp4",
  "size": 1234567890,
  "title": "Movie Title",
  "duration": 7200.5,
  "modified": 1703000000.0,
  "tags": ["Action", "Sci-Fi"],
  "artist": "Director Name",
  "thumbnail": "https://example.com/poster.jpg",
  "description": "Movie description...",
  "premiere_date": "2023-12-15",
    "user_rating": 8.5,
    "playcount": 12,
    "last_played": 1735412345.0
}
```

## Troubleshooting

### NFO File Not Being Read

- Ensure the NFO file has the same base name as the video file
- Check that the NFO file is valid XML
- Verify the file encoding is UTF-8
- Force refresh the video library to rescan

### Metadata Not Showing in UI

- Check that the video library has been scanned
- Verify the NFO file is being read (check logs)
- Force refresh the library
- Clear browser cache if using web UI

### Special Characters in NFO

Always use UTF-8 encoding for NFO files. Escape special XML characters:
- `&` → `&amp;`
- `<` → `&lt;`
- `>` → `&gt;`
- `"` → `&quot;`
- `'` → `&apos;`
