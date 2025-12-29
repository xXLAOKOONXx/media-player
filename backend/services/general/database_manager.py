"""
Unified Database Manager
Manages a single SQLite database for all media player data including:
- Configuration
- Music cache (folders and tracks)
- Video cache (folders and videos)
"""

import sqlite3
import json
import os
import platform
import sys
import hashlib
from datetime import datetime
from pathlib import Path


def get_app_data_dir():
    """Get platform-specific application data directory"""
    if sys.platform == 'win32':
        # Windows: AppData/Local/media-player
        base_dir = os.environ.get('LOCALAPPDATA')
        if not base_dir:
            base_dir = os.path.expanduser('~\\AppData\\Local')
        app_dir = os.path.join(base_dir, 'media-player')
    else:
        # Linux/Mac: ~/.local/share/media-player
        base_dir = os.environ.get('XDG_DATA_HOME')
        if not base_dir:
            base_dir = os.path.expanduser('~/.local/share')
        app_dir = os.path.join(base_dir, 'media-player')
    
    # Create directory if it doesn't exist
    os.makedirs(app_dir, exist_ok=True)
    return app_dir


class DatabaseManager:
    """Manages unified SQLite database for all media player data"""
    
    def __init__(self, db_path=None, timeout=5.0):
        if db_path is None:
            # Use platform-specific app data directory
            app_dir = get_app_data_dir()
            db_path = os.path.join(app_dir, 'media_player.db')
        self.db_path = db_path
        self.timeout = timeout
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with all required tables"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Configuration table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT NOT NULL UNIQUE,
                config_value TEXT NOT NULL,
                updated_at REAL NOT NULL
            )
        ''')
        
        # Music folders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS music_folders (
                id INTEGER PRIMARY KEY,
                path TEXT NOT NULL UNIQUE,
                recursive INTEGER NOT NULL,
                last_scan REAL
            )
        ''')
        
        # Music tracks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS music_tracks (
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
            )
        ''')
        
        # Video folders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_folders (
                id INTEGER PRIMARY KEY,
                path TEXT NOT NULL UNIQUE,
                recursive INTEGER NOT NULL,
                last_scan REAL
            )
        ''')
        
        # Video files table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder_id INTEGER NOT NULL,
                media_id TEXT,
                file_path TEXT NOT NULL UNIQUE,
                file_name TEXT NOT NULL,
                file_size INTEGER,
                title TEXT,
                duration REAL,
                start_time_in_ms INTEGER,
                end_time_in_ms INTEGER,
                last_modified REAL,
                cached_at REAL NOT NULL,
                tags TEXT,
                artist TEXT,
                thumbnail BLOB,
                thumbnail_mime_type TEXT,
                thumbnail_url TEXT,
                description TEXT,
                premiere_date TEXT,
                user_rating REAL,
                FOREIGN KEY (folder_id) REFERENCES video_folders (id) ON DELETE CASCADE
            )
        ''')
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT,
                role TEXT NOT NULL,
                created_at REAL NOT NULL
            )
        ''')
        
        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at REAL NOT NULL,
                expires_at REAL NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Migrate existing videos table to add new columns if they don't exist
        cursor.execute("PRAGMA table_info(videos)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        # Define new columns with their types (hardcoded for safety)
        new_columns = {
            'tags': 'TEXT',
            'artist': 'TEXT',
            'thumbnail': 'BLOB',
            'thumbnail_mime_type': 'TEXT',
            'thumbnail_url': 'TEXT',
            'media_id': 'TEXT',
            'description': 'TEXT',
            'premiere_date': 'TEXT',
            'user_rating': 'REAL',
            'start_time_in_ms': 'INTEGER',
            'end_time_in_ms': 'INTEGER'
        }
        
        # Allowed column types for validation
        allowed_types = {'TEXT', 'REAL', 'INTEGER', 'BLOB'}
        
        for column_name, column_type in new_columns.items():
            if column_name not in existing_columns:
                # Validate column type is allowed
                if column_type not in allowed_types:
                    continue
                
                # Column name validation - ensure it only contains alphanumeric and underscore
                if not column_name.replace('_', '').isalnum():
                    continue
                
                try:
                    # Safe to use f-string here as both values come from our controlled dictionary
                    cursor.execute(f'ALTER TABLE videos ADD COLUMN {column_name} {column_type}')
                except sqlite3.OperationalError:
                    # Column might already exist in some edge cases
                    pass

        # Backfill media_id for existing rows (helps after upgrades)
        if 'media_id' in (existing_columns | set(new_columns.keys())):
            try:
                cursor.execute('SELECT file_path FROM videos WHERE media_id IS NULL OR media_id = ""')
                paths_to_backfill = [row[0] for row in cursor.fetchall() if row and row[0]]
                for file_path in paths_to_backfill:
                    normalized_path = os.path.normpath(file_path)
                    media_id = hashlib.sha256(normalized_path.encode('utf-8', errors='replace')).hexdigest()
                    cursor.execute(
                        'UPDATE videos SET media_id = ? WHERE file_path = ? AND (media_id IS NULL OR media_id = "")',
                        (media_id, normalized_path),
                    )
            except sqlite3.OperationalError:
                # In case the column isn't actually present (corrupt/partial migrations), ignore.
                pass
        
        # Create indexes for faster lookups
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_music_tracks_folder ON music_tracks (folder_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_music_tracks_path ON music_tracks (file_path)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_folder ON videos (folder_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_path ON videos (file_path)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_media_id ON videos (media_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions (user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions (expires_at)')
        
        conn.commit()
        conn.close()
        
        # Initialize default users if they don't exist
        self._init_default_users()
    
    def _get_connection(self):
        """Get a database connection with configured timeout"""
        conn = sqlite3.connect(self.db_path, timeout=self.timeout)

        # Reduce lock contention under concurrent read/write load.
        # These pragmas are safe to apply per-connection; journal_mode is persisted per DB.
        try:
            conn.execute('PRAGMA foreign_keys = ON')
            conn.execute(f'PRAGMA busy_timeout = {int(self.timeout * 1000)}')
            conn.execute('PRAGMA journal_mode = WAL')
            conn.execute('PRAGMA synchronous = NORMAL')
        except sqlite3.OperationalError:
            # Some environments (e.g., read-only DB or older SQLite builds) may reject pragmas.
            pass

        return conn
    
    # Configuration methods
    def get_config(self, key, default=None):
        """Get configuration value"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT config_value FROM config WHERE config_key = ?',
            (key,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            try:
                return json.loads(result[0])
            except json.JSONDecodeError:
                return result[0]
        return default
    
    def set_config(self, key, value):
        """Set configuration value"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        value_str = json.dumps(value) if not isinstance(value, str) else value
        current_time = datetime.now().timestamp()
        
        cursor.execute('''
            INSERT INTO config (config_key, config_value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(config_key) 
            DO UPDATE SET config_value = ?, updated_at = ?
        ''', (key, value_str, current_time, value_str, current_time))
        
        conn.commit()
        conn.close()
    
    def get_all_config(self):
        """Get all configuration"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT config_key, config_value FROM config')
        results = cursor.fetchall()
        conn.close()
        
        config = {}
        for key, value in results:
            try:
                config[key] = json.loads(value)
            except json.JSONDecodeError:
                config[key] = value
        
        return config
    
    # Music folder methods
    def register_music_folder(self, folder_id, path, recursive):
        """Register a music folder in the database"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        recursive_int = 1 if recursive else 0
        
        cursor.execute(
            'SELECT path, recursive FROM music_folders WHERE id = ?',
            (folder_id,)
        )
        existing = cursor.fetchone()
        
        if existing is None:
            cursor.execute('''
                INSERT INTO music_folders (id, path, recursive, last_scan)
                VALUES (?, ?, ?, NULL)
            ''', (folder_id, path, recursive_int))
        else:
            existing_path, existing_recursive = existing[0], existing[1]
            
            if existing_path != path or int(existing_recursive) != recursive_int:
                cursor.execute(
                    'DELETE FROM music_tracks WHERE folder_id = ?',
                    (folder_id,)
                )
                cursor.execute(
                    'UPDATE music_folders SET last_scan = NULL WHERE id = ?',
                    (folder_id,)
                )
            
            cursor.execute(
                'UPDATE music_folders SET path = ?, recursive = ? WHERE id = ?',
                (path, recursive_int, folder_id)
            )
        
        conn.commit()
        conn.close()
    
    def cache_music_tracks(self, folder_id, tracks):
        """Cache music track metadata for a folder"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE music_folders SET last_scan = ? WHERE id = ?',
            (datetime.now().timestamp(), folder_id)
        )
        
        cursor.execute(
            'DELETE FROM music_tracks WHERE folder_id = ?',
            (folder_id,)
        )
        
        current_time = datetime.now().timestamp()
        rows = []
        for track in tracks:
            last_modified = track.get('last_modified')
            rows.append((
                folder_id,
                track['path'],
                track['name'],
                track.get('size', 0),
                track.get('artist'),
                track.get('title'),
                track.get('album'),
                track.get('duration'),
                json.dumps(track.get('tags', [])),
                last_modified,
                current_time,
            ))
        
        cursor.executemany('''
            INSERT INTO music_tracks 
            (folder_id, file_path, file_name, file_size, artist, title, album,
             duration, tags, last_modified, cached_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', rows)
        
        conn.commit()
        conn.close()
    
    def get_cached_music_tracks(self, folder_id):
        """Retrieve cached music tracks for a folder"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT last_scan FROM music_folders WHERE id = ?',
            (folder_id,)
        )
        folder = cursor.fetchone()
        
        if not folder or folder[0] is None:
            conn.close()
            return None
        
        cursor.execute('''
            SELECT file_path, file_name, file_size, artist, title, album,
                   duration, tags, last_modified
            FROM music_tracks
            WHERE folder_id = ?
            ORDER BY artist, title
        ''', (folder_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return []
        
        tracks = []
        for row in rows:
            track = {
                'path': row[0],
                'name': row[1],
                'size': row[2],
                'artist': row[3],
                'title': row[4],
                'album': row[5],
                'duration': row[6],
                'tags': json.loads(row[7]) if row[7] else []
            }
            tracks.append(track)
        
        return tracks
    
    def invalidate_music_folder(self, folder_id):
        """Invalidate cache for a specific music folder"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'DELETE FROM music_tracks WHERE folder_id = ?',
            (folder_id,)
        )
        cursor.execute(
            'UPDATE music_folders SET last_scan = NULL WHERE id = ?',
            (folder_id,)
        )
        
        conn.commit()
        conn.close()
    
    def update_music_track_duration(self, file_path, duration):
        """Update cached duration for a single music track"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE music_tracks SET duration = ? WHERE file_path = ?',
            (duration, file_path)
        )
        
        conn.commit()
        conn.close()
    
    def get_music_cache_stats(self):
        """Get music cache statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM music_folders')
        folder_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM music_tracks')
        track_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(file_size) FROM music_tracks')
        total_size = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'folders': folder_count,
            'tracks': track_count,
            'total_size_bytes': total_size
        }
    
    # Video folder methods
    def register_video_folder(self, folder_id, path, recursive):
        """Register a video folder in the database"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            recursive_int = 1 if recursive else 0

            cursor.execute(
                'SELECT path, recursive FROM video_folders WHERE id = ?',
                (folder_id,),
            )
            existing = cursor.fetchone()

            did_write = False

            if existing is None:
                cursor.execute('''
                    INSERT INTO video_folders (id, path, recursive, last_scan)
                    VALUES (?, ?, ?, NULL)
                ''', (folder_id, path, recursive_int))
                did_write = True
            else:
                existing_path, existing_recursive = existing[0], existing[1]
                changed = (existing_path != path) or (int(existing_recursive) != recursive_int)

                # Avoid unnecessary writes on every request; this reduces SQLite lock pressure.
                if changed:
                    cursor.execute(
                        'DELETE FROM videos WHERE folder_id = ?',
                        (folder_id,),
                    )
                    cursor.execute(
                        'UPDATE video_folders SET last_scan = NULL WHERE id = ?',
                        (folder_id,),
                    )
                    cursor.execute(
                        'UPDATE video_folders SET path = ?, recursive = ? WHERE id = ?',
                        (path, recursive_int, folder_id),
                    )
                    did_write = True

            if did_write:
                conn.commit()
        finally:
            conn.close()
    
    def cache_videos(self, folder_id, videos):
        """Cache video metadata for a folder"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            cursor.execute(
                'UPDATE video_folders SET last_scan = ? WHERE id = ?',
                (datetime.now().timestamp(), folder_id)
            )

            cursor.execute(
                'DELETE FROM videos WHERE folder_id = ?',
                (folder_id,)
            )

            current_time = datetime.now().timestamp()
            rows = []
            for video in videos:
                last_modified = video.get('modified') or video.get('last_modified')
                normalized_path = os.path.normpath(video['path'])
                media_id = hashlib.sha256(normalized_path.encode('utf-8', errors='replace')).hexdigest()
                rows.append((
                    folder_id,
                    media_id,
                    normalized_path,
                    video['name'],
                    video.get('size', 0),
                    video.get('title'),
                    video.get('duration'),
                    video.get('start_time_in_ms'),
                    video.get('end_time_in_ms'),
                    last_modified,
                    current_time,
                    json.dumps(video.get('tags', [])),
                    video.get('artist'),
                    video.get('thumbnail'),  # Binary data
                    video.get('thumbnail_mime_type'),
                    video.get('thumbnail_url'),
                    video.get('description'),
                    video.get('premiere_date'),
                    video.get('user_rating'),
                ))

            cursor.executemany('''
                INSERT INTO videos
                (folder_id, media_id, file_path, file_name, file_size, title, duration,
                 start_time_in_ms, end_time_in_ms,
                 last_modified, cached_at, tags, artist, thumbnail, thumbnail_mime_type,
                 thumbnail_url, description, premiere_date, user_rating)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', rows)

            conn.commit()
        finally:
            conn.close()
    
    def get_cached_videos(self, folder_id):
        """Retrieve cached videos for a folder"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT last_scan FROM video_folders WHERE id = ?',
            (folder_id,)
        )
        folder = cursor.fetchone()
        
        if not folder or folder[0] is None:
            conn.close()
            return None
        
        cursor.execute('''
             SELECT media_id, file_path, file_name, file_size, title, duration,
                 start_time_in_ms, end_time_in_ms,
                 last_modified, tags, artist, thumbnail, thumbnail_mime_type, thumbnail_url,
                 description, premiere_date, user_rating
            FROM videos
            WHERE folder_id = ?
            ORDER BY title, file_name
        ''', (folder_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return []
        
        videos = []
        for row in rows:
            video = {
                'media_id': row[0],
                'path': row[1],
                'name': row[2],
                'size': row[3],
                'title': row[4] or os.path.splitext(row[2])[0],
                'duration': row[5],
                'start_time_in_ms': row[6],
                'end_time_in_ms': row[7],
                'modified': row[8],
                'tags': json.loads(row[9]) if row[9] else [],
                'artist': row[10],
                'has_thumbnail': row[11] is not None,  # Boolean flag instead of binary data
                'thumbnail_url': row[13],
                'description': row[14],
                'premiere_date': row[15],
                'user_rating': row[16]
            }
            videos.append(video)
        
        return videos
    
    def get_video_thumbnail(self, file_path):
        """Get thumbnail data for a specific video by file path
        
        Returns:
            Tuple of (thumbnail_data, mime_type) or (None, None) if not found
        """
        normalized_path = os.path.normpath(file_path)
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT thumbnail, thumbnail_mime_type FROM videos WHERE file_path = ?',
            (normalized_path,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            thumbnail_blob = result[0]
            if isinstance(thumbnail_blob, memoryview):
                thumbnail_blob = thumbnail_blob.tobytes()
            if isinstance(thumbnail_blob, (bytes, bytearray)):
                return bytes(thumbnail_blob), result[1]
        return None, None

    def get_video_thumbnail_by_media_id(self, media_id: str):
        """Get thumbnail data for a specific video by its stable media_id.

        Returns:
            Tuple of (thumbnail_data, mime_type) or (None, None) if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            'SELECT thumbnail, thumbnail_mime_type FROM videos WHERE media_id = ?',
            (media_id,)
        )
        result = cursor.fetchone()
        conn.close()

        if result and result[0]:
            thumbnail_blob = result[0]
            if isinstance(thumbnail_blob, memoryview):
                thumbnail_blob = thumbnail_blob.tobytes()
            if isinstance(thumbnail_blob, (bytes, bytearray)):
                return bytes(thumbnail_blob), result[1]
        return None, None
    
    def invalidate_video_folder(self, folder_id):
        """Invalidate cache for a specific video folder"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'DELETE FROM videos WHERE folder_id = ?',
            (folder_id,)
        )
        cursor.execute(
            'UPDATE video_folders SET last_scan = NULL WHERE id = ?',
            (folder_id,)
        )
        
        conn.commit()
        conn.close()
    
    def update_video_duration(self, file_path, duration):
        """Update cached duration for a single video"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE videos SET duration = ? WHERE file_path = ?',
            (duration, file_path)
        )
        
        conn.commit()
        conn.close()
    
    def get_video_cache_stats(self):
        """Get video cache statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM video_folders')
        folder_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM videos')
        video_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(file_size) FROM videos')
        total_size = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'folders': folder_count,
            'videos': video_count,
            'total_size_bytes': total_size
        }
    
    def clear_all_cache(self):
        """Clear all cached data"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM music_tracks')
        cursor.execute('DELETE FROM music_folders')
        cursor.execute('DELETE FROM videos')
        cursor.execute('DELETE FROM video_folders')
        
        conn.commit()
        conn.close()
    
    # User management methods
    def _init_default_users(self):
        """Initialize default admin and default users if they don't exist"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Check if any users exist
        cursor.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Create default admin user (no password initially)
            current_time = datetime.now().timestamp()
            cursor.execute('''
                INSERT INTO users (username, password_hash, role, created_at)
                VALUES (?, ?, ?, ?)
            ''', ('admin', None, 'admin', current_time))
            
            # Create default user (no password, restricted rights)
            cursor.execute('''
                INSERT INTO users (username, password_hash, role, created_at)
                VALUES (?, ?, ?, ?)
            ''', ('default', None, 'default', current_time))
            
            conn.commit()
        
        conn.close()
    
    def create_user(self, username, password_hash, role):
        """Create a new user"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        current_time = datetime.now().timestamp()
        
        try:
            cursor.execute('''
                INSERT INTO users (username, password_hash, role, created_at)
                VALUES (?, ?, ?, ?)
            ''', (username, password_hash, role, current_time))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return user_id
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    def get_user_by_username(self, username):
        """Get user by username"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, password_hash, role, created_at
            FROM users
            WHERE username = ?
        ''', (username,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'username': row[1],
                'password_hash': row[2],
                'role': row[3],
                'created_at': row[4]
            }
        return None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, password_hash, role, created_at
            FROM users
            WHERE id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'username': row[1],
                'password_hash': row[2],
                'role': row[3],
                'created_at': row[4]
            }
        return None
    
    def get_all_users(self):
        """Get all users"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, role, created_at
            FROM users
            ORDER BY username
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        users = []
        for row in rows:
            users.append({
                'id': row[0],
                'username': row[1],
                'role': row[2],
                'created_at': row[3]
            })
        
        return users
    
    def update_user_password(self, user_id, password_hash):
        """Update user password"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users
            SET password_hash = ?
            WHERE id = ?
        ''', (password_hash, user_id))
        
        conn.commit()
        conn.close()
    
    def delete_user(self, user_id):
        """Delete a user"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        conn.commit()
        conn.close()
    
    def create_session(self, session_id, user_id, expires_at):
        """Create a new session"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        current_time = datetime.now().timestamp()
        
        cursor.execute('''
            INSERT INTO sessions (id, user_id, created_at, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (session_id, user_id, current_time, expires_at))
        
        conn.commit()
        conn.close()
    
    def get_session(self, session_id):
        """Get session by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, user_id, created_at, expires_at
            FROM sessions
            WHERE id = ?
        ''', (session_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'user_id': row[1],
                'created_at': row[2],
                'expires_at': row[3]
            }
        return None
    
    def delete_session(self, session_id):
        """Delete a session"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM sessions WHERE id = ?', (session_id,))
        
        conn.commit()
        conn.close()
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        current_time = datetime.now().timestamp()
        
        cursor.execute('DELETE FROM sessions WHERE expires_at < ?', (current_time,))
        
        conn.commit()
        conn.close()
