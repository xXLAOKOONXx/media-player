# Database Alignment - Implementation Details

## Overview

The media player now uses a **unified SQLite database** (`media_player.db`) that combines all previously separate databases:
- `music_cache.db` (legacy)
- `video_cache.db` (legacy)
- `config.json` (legacy)

## Key Features

### 1. Single Database Instance
All data is now stored in `media_player.db`:
- Configuration settings
- Music folder metadata and track cache
- Video folder metadata and video cache

### 2. Platform-Specific Storage Location
The database is stored in the appropriate per-user application data folder:
- **Windows**: `%LOCALAPPDATA%\media-player\media_player.db` (typically `C:\Users\<username>\AppData\Local\media-player\media_player.db`)
- **Linux**: `~/.local/share/media-player/media_player.db`
- **macOS**: `~/.local/share/media-player/media_player.db`

This ensures:
- Data is stored per-user, not globally
- Each user has their own configuration and cache
- No permission issues with system directories

### 3. Database Schema

#### Config Table
```sql
CREATE TABLE config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT NOT NULL UNIQUE,
    config_value TEXT NOT NULL,
    updated_at REAL NOT NULL
);
```

#### Music Tables
```sql
CREATE TABLE music_folders (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    recursive INTEGER NOT NULL,
    last_scan REAL
);

CREATE TABLE music_tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_id INTEGER NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    file_name TEXT NOT NULL,
    file_size INTEGER,
    artist TEXT,
    title TEXT,
    album TEXT,
    duration REAL,
    tags TEXT,
    last_modified REAL,
    cached_at REAL NOT NULL,
    FOREIGN KEY (folder_id) REFERENCES music_folders (id) ON DELETE CASCADE
);
```

#### Video Tables
```sql
CREATE TABLE video_folders (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    recursive INTEGER NOT NULL,
    last_scan REAL
);

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
    FOREIGN KEY (folder_id) REFERENCES video_folders (id) ON DELETE CASCADE
);
```

## Migration

### Automatic Migration
When the application starts, it automatically:
1. Checks for existing `config.json`
2. Migrates all configuration to the database
3. Renames `config.json` to `config.json.migrated` as a backup

### Legacy Database Files
The old database files (`music_cache.db` and `video_cache.db`) are **not automatically deleted**. They remain as backups. The application will no longer read from or write to them.

You can safely delete these files after verifying the migration worked correctly:
```bash
rm music_cache.db video_cache.db config.json.migrated
```

## API Changes

### No Breaking Changes
All existing APIs continue to work as before. The changes are internal:
- `MusicCache` now uses `DatabaseManager` internally
- `VideoCache` now uses `DatabaseManager` internally
- `app.py` configuration functions now read/write to the database

## Storage Location

The database is automatically stored in the user-specific application data directory:
- Computer A (hostname: `desktop-pc`)

### Windows
```
C:\Users\<username>\AppData\Local\media-player\media_player.db
```

### Linux/macOS
```
~/.local/share/media-player/media_player.db
```

This ensures each user has their own configuration and cache data stored in the appropriate location for their operating system.

## Testing

All existing tests pass with the new implementation:
- Music scanning tests
- Track filtering tests
- Playlist creation tests
- Video cache tests

Additional test coverage:
- Configuration storage tests
- Database migration tests

## Performance

No performance degradation expected:
- Same SQLite backend as before
- Optimized indexes for queries
- Cache invalidation logic unchanged

## Files Modified

1. **New Files**:
   - `backend/database_manager.py` - Unified database manager

2. **Modified Files**:
   - `backend/music_cache.py` - Updated to use DatabaseManager
   - `backend/video_cache.py` - Updated to use DatabaseManager
   - `backend/app.py` - Updated to use database for config storage

3. **Legacy Files** (not deleted, just no longer used):
   - `music_cache.db`
   - `video_cache.db`
   - `config.json` (renamed to `config.json.migrated` after migration)

## Troubleshooting

### Database Location
To find where the database is stored on your system:
```python
from database_manager import get_app_data_dir
print(get_app_data_dir())
```

### Migration Issues
If configuration doesn't migrate properly:
1. Check if `config.json.migrated` exists
2. Manually verify data with: `sqlite3 <path_to_db> "SELECT * FROM config;"`
3. Restore from `config.json.migrated` if needed


### Custom Database Location
If you need to use a custom location:
```python
from database_manager import DatabaseManager
db = DatabaseManager('/path/to/custom/location/media_player.db')
```

## Future Enhancements

Possible future improvements:
1. Export/import configurations
2. Database vacuum/optimization commands
3. Database encryption for sensitive data
4. Cloud sync support
