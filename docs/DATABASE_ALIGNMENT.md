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

### 2. Device-Aware Configuration
The database uses the **computer's hostname** (via `platform.node()`) to identify different devices. This enables:
- Multiple devices to share the same database file (e.g., on a network share)
- Each device maintains its own configuration and cache
- No conflicts when different devices access the same database

### 3. Database Schema

#### Config Table
```sql
CREATE TABLE config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_name TEXT NOT NULL,
    config_key TEXT NOT NULL,
    config_value TEXT NOT NULL,
    updated_at REAL NOT NULL,
    UNIQUE(device_name, config_key)
);
```

#### Music Tables
```sql
CREATE TABLE music_folders (
    device_name TEXT NOT NULL,
    id INTEGER NOT NULL,
    path TEXT NOT NULL,
    recursive INTEGER NOT NULL,
    last_scan REAL,
    PRIMARY KEY (device_name, id)
);

CREATE TABLE music_tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_name TEXT NOT NULL,
    folder_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_size INTEGER,
    artist TEXT,
    title TEXT,
    album TEXT,
    duration REAL,
    tags TEXT,
    last_modified REAL,
    cached_at REAL NOT NULL,
    UNIQUE(device_name, folder_id, file_path)
);
```

#### Video Tables
```sql
CREATE TABLE video_folders (
    device_name TEXT NOT NULL,
    id INTEGER NOT NULL,
    path TEXT NOT NULL,
    recursive INTEGER NOT NULL,
    last_scan REAL,
    PRIMARY KEY (device_name, id)
);

CREATE TABLE videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_name TEXT NOT NULL,
    folder_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_size INTEGER,
    title TEXT,
    duration REAL,
    last_modified REAL,
    cached_at REAL NOT NULL,
    UNIQUE(device_name, folder_id, file_path)
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

## Multi-Device Support Example

### Scenario
You have two computers sharing a network drive:
- Computer A (hostname: `desktop-pc`)
- Computer B (hostname: `laptop`)

### Configuration
1. Place `media_player.db` on the shared network drive
2. Point both installations to use the same database file
3. Each device will have its own configuration in the database:
   - `desktop-pc` → its own music folders, video folders, settings
   - `laptop` → its own music folders, video folders, settings

### Benefits
- No configuration conflicts
- Each device can have different paths (since they might mount shares differently)
- Cache is device-specific (optimized for each device's access patterns)
- Shared database means easier backup and management

## Testing

All existing tests pass with the new implementation:
- Music scanning tests
- Track filtering tests
- Playlist creation tests
- Video cache tests

Additional test coverage:
- Device isolation tests
- Configuration storage tests
- Database migration tests

## Performance

No performance degradation expected:
- Same SQLite backend as before
- Optimized indexes for device-specific queries
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

### Database Locked Error
If you get "database is locked" errors with a network database:
1. Ensure only one instance is writing at a time
2. Consider using a longer timeout: `DatabaseManager(db_path, timeout=30.0)`
3. Check network connection stability

### Migration Issues
If configuration doesn't migrate properly:
1. Check if `config.json.migrated` exists
2. Manually verify data with: `sqlite3 media_player.db "SELECT * FROM config;"`
3. Restore from `config.json.migrated` if needed

### Device Name Issues
If you want to override the device name:
```python
db = DatabaseManager()
db.device_name = "custom-device-name"
```

## Future Enhancements

Possible future improvements:
1. Add device management UI (view all devices using the database)
2. Export/import device configurations
3. Shared playlists across devices
4. Database vacuum/optimization commands
5. Database encryption for sensitive data
