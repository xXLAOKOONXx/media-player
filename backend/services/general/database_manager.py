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
import time
import platform
import sys
import hashlib
import shutil
import tempfile
import mimetypes
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
                media_id TEXT,
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

        # Video series table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_series (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder_id INTEGER NOT NULL,
                full_path TEXT NOT NULL,
                title TEXT,
                user_rating REAL,
                tags TEXT,
                artists TEXT,
                cover TEXT,
                UNIQUE (folder_id, full_path),
                FOREIGN KEY (folder_id) REFERENCES video_folders (id) ON DELETE CASCADE
            )
        ''')

        # Video seasons table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_seasons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                series_id INTEGER NOT NULL,
                full_path TEXT NOT NULL,
                title TEXT,
                user_rating REAL,
                tags TEXT,
                artists TEXT,
                cover TEXT,
                index_number INTEGER,
                UNIQUE (series_id, full_path),
                FOREIGN KEY (series_id) REFERENCES video_series (id) ON DELETE CASCADE
            )
        ''')
        
        # Video files table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder_id INTEGER NOT NULL,
                series_id INTEGER,
                season_id INTEGER,
                media_id TEXT,
                file_path TEXT NOT NULL UNIQUE,
                file_name TEXT NOT NULL,
                file_size INTEGER,
                title TEXT,
                index_number INTEGER,
                duration REAL,
                start_time_in_ms INTEGER,
                end_time_in_ms INTEGER,
                last_modified REAL,
                cached_at REAL NOT NULL,
                tags TEXT,
                artist TEXT,
                thumbnail BLOB,
                thumbnail_mime_type TEXT,
                thumbnail_file TEXT,
                thumbnail_url TEXT,
                description TEXT,
                premiere_date TEXT,
                user_rating REAL,
                FOREIGN KEY (folder_id) REFERENCES video_folders (id) ON DELETE CASCADE
            )
        ''')

        # Generic artwork thumbnails (e.g., Series/Season posters).
        # Stored on disk under the same thumbs/ layout as video thumbnails.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_artwork (
                art_id TEXT PRIMARY KEY,
                source_path TEXT,
                source_mtime REAL,
                thumbnail_file TEXT,
                thumbnail_mime_type TEXT,
                updated_at REAL NOT NULL
            )
        ''')
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT,
                role TEXT NOT NULL,
                preferred_language TEXT NOT NULL DEFAULT 'eng',
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

        # Saved per-user audio/subtitle defaults for videos/series/seasons.
        # NOTE: name spelling matches existing UI request ("prefered_").
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prefered_channel (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                scope_type TEXT NOT NULL,
                scope_key TEXT NOT NULL,
                channel INTEGER NOT NULL,
                updated_at REAL NOT NULL,
                UNIQUE (user_id, scope_type, scope_key),
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prefered_subtitle (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                scope_type TEXT NOT NULL,
                scope_key TEXT NOT NULL,
                subtitle INTEGER,
                updated_at REAL NOT NULL,
                UNIQUE (user_id, scope_type, scope_key),
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Migrate existing videos table to add new columns if they don't exist
        cursor.execute("PRAGMA table_info(videos)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        # Migrate existing music_tracks table to add media_id if missing
        cursor.execute("PRAGMA table_info(music_tracks)")
        existing_music_columns = {row[1] for row in cursor.fetchall()}
        if 'media_id' not in existing_music_columns:
            try:
                cursor.execute('ALTER TABLE music_tracks ADD COLUMN media_id TEXT')
                existing_music_columns.add('media_id')
            except sqlite3.OperationalError:
                pass
        
        # Define new columns with their types (hardcoded for safety)
        new_columns = {
            'tags': 'TEXT',
            'artist': 'TEXT',
            'thumbnail': 'BLOB',
            'thumbnail_mime_type': 'TEXT',
            'thumbnail_file': 'TEXT',
            'thumbnail_url': 'TEXT',
            'media_id': 'TEXT',
            'description': 'TEXT',
            'premiere_date': 'TEXT',
            'user_rating': 'REAL',
            'start_time_in_ms': 'INTEGER',
            'end_time_in_ms': 'INTEGER',
            'index_number': 'INTEGER',
            'series_id': 'INTEGER',
            'season_id': 'INTEGER'
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

        # Migrate existing users table to add preferred_language if missing
        cursor.execute("PRAGMA table_info(users)")
        existing_user_columns = {row[1] for row in cursor.fetchall()}
        if 'preferred_language' not in existing_user_columns:
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN preferred_language TEXT NOT NULL DEFAULT 'eng'")
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute("UPDATE users SET preferred_language='eng' WHERE preferred_language IS NULL")
            except sqlite3.OperationalError:
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

        # Backfill media_id for existing music tracks
        if 'media_id' in existing_music_columns:
            try:
                cursor.execute('SELECT file_path FROM music_tracks WHERE media_id IS NULL OR media_id = ""')
                music_paths_to_backfill = [row[0] for row in cursor.fetchall() if row and row[0]]
                for file_path in music_paths_to_backfill:
                    normalized_path = os.path.normpath(file_path)
                    media_id = hashlib.sha256(normalized_path.encode('utf-8', errors='replace')).hexdigest()
                    cursor.execute(
                        'UPDATE music_tracks SET media_id = ? WHERE file_path = ? AND (media_id IS NULL OR media_id = "")',
                        (media_id, normalized_path),
                    )
            except sqlite3.OperationalError:
                pass
        
        # Create indexes for faster lookups
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_music_tracks_folder ON music_tracks (folder_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_music_tracks_path ON music_tracks (file_path)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_music_tracks_media_id ON music_tracks (media_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_folder ON videos (folder_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_path ON videos (file_path)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_media_id ON videos (media_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_series_id ON videos (series_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_season_id ON videos (season_id)')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_video_artwork_source_path ON video_artwork (source_path)')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_video_series_folder ON video_series (folder_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_video_series_full_path ON video_series (full_path)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_video_seasons_series ON video_seasons (series_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_video_seasons_full_path ON video_seasons (full_path)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions (user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions (expires_at)')
        
        conn.commit()
        conn.close()

    def get_video_series_season_ids_by_media_id(self, media_id: str) -> tuple[int | None, int | None]:
        """Return (series_id, season_id) for a video media_id, if known."""
        if not isinstance(media_id, str) or not media_id:
            return None, None

        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT series_id, season_id FROM videos WHERE media_id = ?', (media_id,))
            row = cursor.fetchone()
        finally:
            conn.close()

        if not row:
            return None, None

        series_id = row[0] if isinstance(row[0], int) else None
        season_id = row[1] if isinstance(row[1], int) else None
        return series_id, season_id

    def upsert_prefered_channel(self, *, user_id: int, scope_type: str, scope_key: str, channel: int) -> None:
        """Insert or update a saved default audio channel (MPV aid) for a user + scope."""
        if not isinstance(user_id, int):
            raise ValueError('user_id must be int')
        if not isinstance(scope_type, str) or not scope_type:
            raise ValueError('scope_type is required')
        if not isinstance(scope_key, str) or not scope_key:
            raise ValueError('scope_key is required')
        if not isinstance(channel, int) or channel < 0:
            raise ValueError('channel must be a non-negative int')

        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                '''
                INSERT INTO prefered_channel (user_id, scope_type, scope_key, channel, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, scope_type, scope_key)
                DO UPDATE SET channel = excluded.channel, updated_at = excluded.updated_at
                ''',
                (user_id, scope_type, scope_key, channel, time.time()),
            )
            conn.commit()
        finally:
            conn.close()

    def get_prefered_channel(self, *, user_id: int, scope_type: str, scope_key: str) -> int | None:
        """Get saved default audio channel (MPV aid) for a user + scope."""
        if not isinstance(user_id, int):
            return None
        if not isinstance(scope_type, str) or not scope_type:
            return None
        if not isinstance(scope_key, str) or not scope_key:
            return None

        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                'SELECT channel FROM prefered_channel WHERE user_id = ? AND scope_type = ? AND scope_key = ?',
                (user_id, scope_type, scope_key),
            )
            row = cursor.fetchone()
        finally:
            conn.close()
        if not row:
            return None
        try:
            return int(row[0])
        except Exception:
            return None

    def upsert_prefered_subtitle(self, *, user_id: int, scope_type: str, scope_key: str, subtitle: int | None) -> None:
        """Insert or update a saved default subtitle track (MPV sid).

        subtitle:
            - int >= 0: selected subtitle track id
            - None: subtitles off
        """
        if not isinstance(user_id, int):
            raise ValueError('user_id must be int')
        if not isinstance(scope_type, str) or not scope_type:
            raise ValueError('scope_type is required')
        if not isinstance(scope_key, str) or not scope_key:
            raise ValueError('scope_key is required')
        if subtitle is not None:
            if not isinstance(subtitle, int) or subtitle < 0:
                raise ValueError('subtitle must be None or a non-negative int')

        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                '''
                INSERT INTO prefered_subtitle (user_id, scope_type, scope_key, subtitle, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, scope_type, scope_key)
                DO UPDATE SET subtitle = excluded.subtitle, updated_at = excluded.updated_at
                ''',
                (user_id, scope_type, scope_key, subtitle, time.time()),
            )
            conn.commit()
        finally:
            conn.close()

    def get_prefered_subtitle(self, *, user_id: int, scope_type: str, scope_key: str) -> int | None:
        """Get saved default subtitle track (MPV sid) for a user + scope.

        Returns:
            - int >= 0: subtitle track id
            - None: no preference saved OR preference is "off"
        """
        if not isinstance(user_id, int):
            return None
        if not isinstance(scope_type, str) or not scope_type:
            return None
        if not isinstance(scope_key, str) or not scope_key:
            return None

        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                'SELECT subtitle FROM prefered_subtitle WHERE user_id = ? AND scope_type = ? AND scope_key = ?',
                (user_id, scope_type, scope_key),
            )
            row = cursor.fetchone()
        finally:
            conn.close()
        if not row:
            return None
        if row[0] is None:
            return None
        try:
            return int(row[0])
        except Exception:
            return None
        
        # Initialize default users if they don't exist
        self._init_default_users()

    def get_prefered_subtitle_with_presence(
        self, *, user_id: int, scope_type: str, scope_key: str
    ) -> tuple[bool, int | None]:
        """Return (exists, subtitle).

        `subtitle` may be NULL to represent "Off".
        """
        if not isinstance(user_id, int):
            return (False, None)
        if not isinstance(scope_type, str) or not scope_type:
            return (False, None)
        if not isinstance(scope_key, str) or not scope_key:
            return (False, None)

        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                'SELECT subtitle FROM prefered_subtitle WHERE user_id = ? AND scope_type = ? AND scope_key = ?',
                (user_id, scope_type, scope_key),
            )
            row = cursor.fetchone()
        finally:
            conn.close()

        if not row:
            return (False, None)
        return (True, row[0])
    
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

    def _get_db_dir(self) -> str:
        return os.path.dirname(os.path.abspath(self.db_path))

    def _get_thumbs_root_dir(self) -> str:
        return os.path.join(self._get_db_dir(), 'thumbs')

    @staticmethod
    def _thumb_ext_from_mime(mime_type: str | None) -> str:
        if not mime_type or not isinstance(mime_type, str):
            return 'jpg'
        mt = mime_type.lower().strip()
        if 'png' in mt:
            return 'png'
        if 'webp' in mt:
            return 'webp'
        if 'gif' in mt:
            return 'gif'
        if 'jpeg' in mt or 'jpg' in mt:
            return 'jpg'
        return 'bin'

    def _persist_thumbnail_file(self, media_id: str, data: bytes, mime_type: str | None) -> str:
        """Write thumbnail bytes to disk and return a DB-storable relative path.

        Layout: <db_dir>/thumbs/<first4>/<media_id>.<ext>
        """
        if not isinstance(media_id, str) or not media_id:
            raise ValueError('media_id required')
        if not isinstance(data, (bytes, bytearray)) or not data:
            raise ValueError('thumbnail bytes required')

        prefix = media_id[:4] if len(media_id) >= 4 else media_id
        ext = self._thumb_ext_from_mime(mime_type)

        root = self._get_thumbs_root_dir()
        subdir = os.path.join(root, prefix)
        os.makedirs(subdir, exist_ok=True)

        abs_path = os.path.join(subdir, f'{media_id}.{ext}')

        fd, tmp_path = tempfile.mkstemp(prefix=f'{media_id}.', suffix='.tmp', dir=subdir)
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(data)
            os.replace(tmp_path, abs_path)
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

        return os.path.relpath(abs_path, self._get_db_dir())

    def _read_thumbnail_file(self, thumbnail_file: str) -> bytes | None:
        if not isinstance(thumbnail_file, str) or not thumbnail_file:
            return None
        abs_path = thumbnail_file
        if not os.path.isabs(abs_path):
            abs_path = os.path.join(self._get_db_dir(), thumbnail_file)
        try:
            if not os.path.exists(abs_path):
                return None
            with open(abs_path, 'rb') as f:
                return f.read()
        except Exception:
            return None

    def _delete_thumbnail_file(self, thumbnail_file: str | None) -> None:
        if not thumbnail_file or not isinstance(thumbnail_file, str):
            return
        abs_path = thumbnail_file
        if not os.path.isabs(abs_path):
            abs_path = os.path.join(self._get_db_dir(), thumbnail_file)
        try:
            if os.path.exists(abs_path):
                os.remove(abs_path)
        except Exception:
            pass

    @staticmethod
    def _mime_from_image_path(path: str) -> str | None:
        if not isinstance(path, str) or not path:
            return None
        mime, _ = mimetypes.guess_type(path)
        if isinstance(mime, str) and mime.startswith('image/'):
            return mime
        ext = os.path.splitext(path)[1].lower().lstrip('.')
        if ext in ('jpg', 'jpeg'):
            return 'image/jpeg'
        if ext == 'png':
            return 'image/png'
        if ext == 'webp':
            return 'image/webp'
        if ext == 'gif':
            return 'image/gif'
        return None

    def ensure_video_artwork_from_source(self, art_id: str, source_path: str) -> bool:
        """Ensure a poster/cover image is cached on disk and tracked in DB.

        This is used for Series/Season posters that are not tied to a video row.
        Returns True if artwork is available after the call, False otherwise.
        """
        if not isinstance(art_id, str) or not art_id.strip():
            return False
        if not isinstance(source_path, str) or not source_path:
            return False

        art_id = art_id.strip()

        try:
            if not os.path.exists(source_path) or not os.path.isfile(source_path):
                return False
            source_mtime = os.path.getmtime(source_path)
        except Exception:
            return False

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            'SELECT source_mtime, thumbnail_file FROM video_artwork WHERE art_id = ?',
            (art_id,),
        )
        row = cursor.fetchone()

        if row:
            cached_mtime, thumb_file = row
            if cached_mtime is not None and cached_mtime == source_mtime and thumb_file:
                abs_path = thumb_file
                if not os.path.isabs(abs_path):
                    abs_path = os.path.join(self._get_db_dir(), thumb_file)
                if os.path.exists(abs_path):
                    conn.close()
                    return True

        # Cache miss or stale: (re)read and persist.
        try:
            with open(source_path, 'rb') as f:
                data = f.read()
            if not data:
                conn.close()
                return False
        except Exception:
            conn.close()
            return False

        mime_type = self._mime_from_image_path(source_path)
        try:
            new_thumb_file = self._persist_thumbnail_file(art_id, data, mime_type)
        except Exception:
            conn.close()
            return False

        # Cleanup old file if it differs.
        if row:
            old_thumb_file = row[1]
            if old_thumb_file and old_thumb_file != new_thumb_file:
                self._delete_thumbnail_file(old_thumb_file)

        now = datetime.now().timestamp()
        cursor.execute(
            '''
            INSERT INTO video_artwork (art_id, source_path, source_mtime, thumbnail_file, thumbnail_mime_type, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(art_id) DO UPDATE SET
                source_path = excluded.source_path,
                source_mtime = excluded.source_mtime,
                thumbnail_file = excluded.thumbnail_file,
                thumbnail_mime_type = excluded.thumbnail_mime_type,
                updated_at = excluded.updated_at
            ''',
            (art_id, source_path, source_mtime, new_thumb_file, mime_type, now),
        )
        conn.commit()
        conn.close()
        return True

    def get_video_artwork_thumbnail(self, art_id: str):
        """Get cached artwork thumbnail bytes by art_id.

        Returns:
            (bytes, mime_type) or (None, None)
        """
        if not isinstance(art_id, str) or not art_id.strip():
            return None, None

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT thumbnail_file, thumbnail_mime_type FROM video_artwork WHERE art_id = ?',
            (art_id.strip(),),
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None, None

        thumb_file, mime_type = row
        if not thumb_file:
            return None, None

        data = self._read_thumbnail_file(thumb_file)
        if isinstance(data, (bytes, bytearray)) and data:
            return bytes(data), mime_type

        return None, None
    
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
            file_path = os.path.normpath(track['path'])
            media_id = track.get('media_id')
            if not media_id and isinstance(file_path, str) and file_path:
                media_id = hashlib.sha256(file_path.encode('utf-8', errors='replace')).hexdigest()
            rows.append((
                folder_id,
                media_id,
                file_path,
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
            (folder_id, media_id, file_path, file_name, file_size, artist, title, album,
             duration, tags, last_modified, cached_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            SELECT media_id, file_path, file_name, file_size, artist, title, album,
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
                'media_id': row[0],
                'path': row[1],
                'name': row[2],
                'size': row[3],
                'artist': row[4],
                'title': row[5],
                'album': row[6],
                'duration': row[7],
                'tags': json.loads(row[8]) if row[8] else []
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

    def get_music_file_path_by_media_id(self, media_id: str):
        """Resolve a music media_id to a file path from the cache."""
        if not isinstance(media_id, str) or not media_id:
            return None

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT file_path FROM music_tracks WHERE media_id = ? LIMIT 1', (media_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def get_music_tracks_by_media_ids(self, media_ids):
        """Return cached track info for a set of media_ids.

        Returns dict: { media_id: { path, name, artist, title, album, duration, tags } }
        """
        if not isinstance(media_ids, list) or not media_ids:
            return {}

        filtered = [mid for mid in media_ids if isinstance(mid, str) and mid]
        if not filtered:
            return {}

        placeholders = ','.join(['?'] * len(filtered))
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f'''
                SELECT media_id, file_path, file_name, artist, title, album, duration, tags
                FROM music_tracks
                WHERE media_id IN ({placeholders})
            ''',
            tuple(filtered),
        )
        rows = cursor.fetchall()
        conn.close()

        result = {}
        for row in rows:
            mid = row[0]
            result[mid] = {
                'path': row[1],
                'name': row[2],
                'artist': row[3],
                'title': row[4],
                'album': row[5],
                'duration': row[6],
                'tags': json.loads(row[7]) if row[7] else [],
            }
        return result
    
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
                        'SELECT thumbnail_file FROM videos WHERE folder_id = ?',
                        (folder_id,),
                    )
                    for (thumbnail_file,) in cursor.fetchall() or []:
                        self._delete_thumbnail_file(thumbnail_file)
                    cursor.execute(
                        'DELETE FROM videos WHERE folder_id = ?',
                        (folder_id,),
                    )
                    cursor.execute(
                        'DELETE FROM video_series WHERE folder_id = ?',
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
    
    def cache_videos(self, folder_id, videos, series_tree=None):
        """Cache video metadata for a folder.

        If `series_tree` is provided, Series and Seasons are persisted into
        `video_series` and `video_seasons`, and videos will reference them via
        `series_id` and `season_id`.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            cursor.execute(
                'SELECT path, recursive FROM video_folders WHERE id = ?',
                (folder_id,),
            )
            folder_row = cursor.fetchone()
            folder_path = folder_row[0] if folder_row else None
            folder_recursive = bool(int(folder_row[1])) if folder_row and folder_row[1] is not None else False

            cursor.execute(
                'UPDATE video_folders SET last_scan = ? WHERE id = ?',
                (datetime.now().timestamp(), folder_id)
            )

            cursor.execute(
                'SELECT thumbnail_file FROM videos WHERE folder_id = ?',
                (folder_id,),
            )
            for (thumbnail_file,) in cursor.fetchall() or []:
                self._delete_thumbnail_file(thumbnail_file)

            cursor.execute(
                'DELETE FROM videos WHERE folder_id = ?',
                (folder_id,)
            )

            # Clear series/seasons for this folder; they will be rebuilt.
            cursor.execute(
                'DELETE FROM video_series WHERE folder_id = ?',
                (folder_id,)
            )

            series_id_by_full_path: dict[str, int] = {}
            season_id_by_full_path: dict[str, int] = {}

            # Persist series/seasons only for recursive folders.
            if folder_recursive and isinstance(series_tree, list) and folder_path:
                for series in series_tree:
                    if not isinstance(series, dict):
                        continue
                    full_path = series.get('full_path')
                    if not isinstance(full_path, str) or not full_path:
                        continue

                    title = series.get('title') if isinstance(series.get('title'), str) else None
                    user_rating = series.get('user_rating') if isinstance(series.get('user_rating'), (int, float)) else None
                    tags = series.get('tags') if isinstance(series.get('tags'), list) else []
                    artists = series.get('artists') if isinstance(series.get('artists'), list) else []
                    cover = series.get('cover') if isinstance(series.get('cover'), str) else None

                    cursor.execute(
                        '''
                            INSERT INTO video_series (folder_id, full_path, title, user_rating, tags, artists, cover)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''',
                        (
                            folder_id,
                            os.path.normpath(full_path),
                            title,
                            float(user_rating) if isinstance(user_rating, (int, float)) else None,
                            json.dumps(tags),
                            json.dumps(artists),
                            cover,
                        ),
                    )
                    series_db_id = int(cursor.lastrowid)
                    series_id_by_full_path[os.path.normpath(full_path)] = series_db_id

                    seasons = series.get('seasons')
                    if isinstance(seasons, list):
                        for season in seasons:
                            if not isinstance(season, dict):
                                continue
                            season_full_path = season.get('full_path')
                            if not isinstance(season_full_path, str) or not season_full_path:
                                continue
                            season_title = season.get('title') if isinstance(season.get('title'), str) else None
                            season_user_rating = season.get('user_rating') if isinstance(season.get('user_rating'), (int, float)) else None
                            season_tags = season.get('tags') if isinstance(season.get('tags'), list) else []
                            season_artists = season.get('artists') if isinstance(season.get('artists'), list) else []
                            season_cover = season.get('cover') if isinstance(season.get('cover'), str) else None
                            season_index = season.get('index_number') if isinstance(season.get('index_number'), int) else None

                            cursor.execute(
                                '''
                                    INSERT INTO video_seasons (series_id, full_path, title, user_rating, tags, artists, cover, index_number)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                ''',
                                (
                                    series_db_id,
                                    os.path.normpath(season_full_path),
                                    season_title,
                                    float(season_user_rating) if isinstance(season_user_rating, (int, float)) else None,
                                    json.dumps(season_tags),
                                    json.dumps(season_artists),
                                    season_cover,
                                    season_index,
                                ),
                            )
                            season_db_id = int(cursor.lastrowid)
                            season_id_by_full_path[os.path.normpath(season_full_path)] = season_db_id

            current_time = datetime.now().timestamp()
            rows = []
            for video in videos:
                last_modified = video.get('modified') or video.get('last_modified')
                normalized_path = os.path.normpath(video['path'])
                media_id = hashlib.sha256(normalized_path.encode('utf-8', errors='replace')).hexdigest()

                thumb_blob = video.get('thumbnail')
                thumb_mime = video.get('thumbnail_mime_type')
                thumb_file = None
                if isinstance(thumb_blob, (bytes, bytearray, memoryview)):
                    try:
                        thumb_file = self._persist_thumbnail_file(media_id, bytes(thumb_blob), thumb_mime)
                        thumb_blob = None
                    except Exception:
                        # Fall back to DB blob on any failure.
                        thumb_file = None

                series_id = None
                season_id = None
                if folder_recursive and folder_path:
                    try:
                        rel = os.path.relpath(normalized_path, folder_path)
                        parts = [p for p in rel.split(os.sep) if p and p not in ('.', '..')]
                        if len(parts) >= 2:
                            series_full_path = os.path.normpath(os.path.join(folder_path, parts[0]))
                            series_id = series_id_by_full_path.get(series_full_path)
                        if len(parts) >= 3:
                            season_full_path = os.path.normpath(os.path.join(folder_path, parts[0], parts[1]))
                            season_id = season_id_by_full_path.get(season_full_path)
                    except Exception:
                        series_id = None
                        season_id = None

                rows.append((
                    folder_id,
                    series_id,
                    season_id,
                    media_id,
                    normalized_path,
                    video['name'],
                    video.get('size', 0),
                    video.get('title'),
                    video.get('index_number'),
                    video.get('duration'),
                    video.get('start_time_in_ms'),
                    video.get('end_time_in_ms'),
                    last_modified,
                    current_time,
                    json.dumps(video.get('tags', [])),
                    video.get('artist'),
                    thumb_blob,
                    thumb_mime,
                    thumb_file,
                    video.get('thumbnail_url'),
                    video.get('description'),
                    video.get('premiere_date'),
                    video.get('user_rating'),
                ))

            cursor.executemany('''
                INSERT INTO videos
                (folder_id, series_id, season_id, media_id, file_path, file_name, file_size, title, index_number, duration,
                 start_time_in_ms, end_time_in_ms,
                 last_modified, cached_at, tags, artist, thumbnail, thumbnail_mime_type,
                 thumbnail_file, thumbnail_url, description, premiere_date, user_rating)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', rows)

            conn.commit()
        finally:
            conn.close()

    def update_video_folder_last_scan(self, folder_id: int, timestamp: float | None = None) -> None:
        """Update the folder's last_scan timestamp."""
        if timestamp is None:
            timestamp = datetime.now().timestamp()
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE video_folders SET last_scan = ? WHERE id = ?',
                (float(timestamp), int(folder_id)),
            )
            conn.commit()
        finally:
            conn.close()

    def get_video_cache_freshness(self, file_path: str) -> dict | None:
        """Return minimal cache freshness info for a single video.

        Returns dict with keys: cached_at, last_modified, folder_id.
        """
        if not isinstance(file_path, str) or not file_path:
            return None
        normalized_path = os.path.normpath(file_path)
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT folder_id, cached_at, last_modified FROM videos WHERE file_path = ?',
                (normalized_path,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                'folder_id': row[0],
                'cached_at': row[1],
                'last_modified': row[2],
            }
        finally:
            conn.close()

    def get_cached_video_by_path(self, file_path: str) -> dict | None:
        """Retrieve a single cached video dict by file path.

        Returns None if not found.
        """
        if not isinstance(file_path, str) or not file_path:
            return None
        normalized_path = os.path.normpath(file_path)
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            try:
                cursor.execute('''
                    SELECT v.media_id, v.file_path, v.file_name, v.file_size, v.title, v.index_number, v.duration,
                           v.start_time_in_ms, v.end_time_in_ms,
                           v.last_modified, v.tags, v.artist, v.thumbnail, v.thumbnail_mime_type, v.thumbnail_file, v.thumbnail_url,
                           v.description, v.premiere_date, v.user_rating,
                           vs.full_path AS series_full_path,
                           vsea.full_path AS season_full_path
                    FROM videos v
                    LEFT JOIN video_series vs ON vs.id = v.series_id
                    LEFT JOIN video_seasons vsea ON vsea.id = v.season_id
                    WHERE v.file_path = ?
                ''', (normalized_path,))
                row = cursor.fetchone()
                if not row:
                    return None
                series_full_path = row[19] if len(row) > 19 else None
                season_full_path = row[20] if len(row) > 20 else None

                video = {
                    'media_id': row[0],
                    'path': row[1],
                    'name': row[2],
                    'size': row[3],
                    'title': row[4] or os.path.splitext(row[2])[0],
                    'index_number': row[5],
                    'duration': row[6],
                    'start_time_in_ms': row[7],
                    'end_time_in_ms': row[8],
                    'modified': row[9],
                    'tags': json.loads(row[10]) if row[10] else [],
                    'artist': row[11],
                    'has_thumbnail': (row[12] is not None) or (row[14] is not None),
                    'thumbnail_url': row[15],
                    'description': row[16],
                    'premiere_date': row[17],
                    'user_rating': row[18],
                }
                if isinstance(series_full_path, str) and series_full_path.strip():
                    video['series'] = os.path.basename(series_full_path.strip())
                if isinstance(season_full_path, str) and season_full_path.strip():
                    video['season'] = os.path.basename(season_full_path.strip())
                return video
            except sqlite3.OperationalError:
                try:
                    cursor.execute('''
                        SELECT media_id, file_path, file_name, file_size, title, index_number, duration,
                               start_time_in_ms, end_time_in_ms,
                               last_modified, tags, artist, thumbnail, thumbnail_mime_type, thumbnail_file, thumbnail_url,
                               description, premiere_date, user_rating
                        FROM videos
                        WHERE file_path = ?
                    ''', (normalized_path,))
                    row = cursor.fetchone()
                    if not row:
                        return None
                    return {
                        'media_id': row[0],
                        'path': row[1],
                        'name': row[2],
                        'size': row[3],
                        'title': row[4] or os.path.splitext(row[2])[0],
                        'index_number': row[5],
                        'duration': row[6],
                        'start_time_in_ms': row[7],
                        'end_time_in_ms': row[8],
                        'modified': row[9],
                        'tags': json.loads(row[10]) if row[10] else [],
                        'artist': row[11],
                        'has_thumbnail': (row[12] is not None) or (row[14] is not None),
                        'thumbnail_url': row[15],
                        'description': row[16],
                        'premiere_date': row[17],
                        'user_rating': row[18],
                    }
                except sqlite3.OperationalError:
                    cursor.execute('''
                        SELECT media_id, file_path, file_name, file_size, title, index_number, duration,
                               start_time_in_ms, end_time_in_ms,
                               last_modified, tags, artist, thumbnail, thumbnail_mime_type, thumbnail_url,
                               description, premiere_date, user_rating
                        FROM videos
                        WHERE file_path = ?
                    ''', (normalized_path,))
                    row = cursor.fetchone()
                    if not row:
                        return None
                    return {
                        'media_id': row[0],
                        'path': row[1],
                        'name': row[2],
                        'size': row[3],
                        'title': row[4] or os.path.splitext(row[2])[0],
                        'index_number': row[5],
                        'duration': row[6],
                        'start_time_in_ms': row[7],
                        'end_time_in_ms': row[8],
                        'modified': row[9],
                        'tags': json.loads(row[10]) if row[10] else [],
                        'artist': row[11],
                        'has_thumbnail': row[12] is not None,
                        'thumbnail_url': row[14],
                        'description': row[15],
                        'premiere_date': row[16],
                        'user_rating': row[17],
                    }
        finally:
            conn.close()

    def upsert_video(self, folder_id: int, video: dict, *, series_id: int | None = None, season_id: int | None = None) -> None:
        """Insert or update a single video row."""
        if not isinstance(video, dict):
            return
        file_path = video.get('path')
        file_name = video.get('name')
        if not isinstance(file_path, str) or not file_path:
            return
        if not isinstance(file_name, str) or not file_name:
            return

        normalized_path = os.path.normpath(file_path)
        media_id = hashlib.sha256(normalized_path.encode('utf-8', errors='replace')).hexdigest()
        current_time = datetime.now().timestamp()
        last_modified = video.get('modified') or video.get('last_modified')

        thumb_blob = video.get('thumbnail')
        thumb_mime = video.get('thumbnail_mime_type')
        thumb_file = None
        if isinstance(thumb_blob, (bytes, bytearray, memoryview)):
            try:
                thumb_file = self._persist_thumbnail_file(media_id, bytes(thumb_blob), thumb_mime)
                thumb_blob = None
            except Exception:
                thumb_file = None

        row = (
            int(folder_id),
            series_id,
            season_id,
            media_id,
            normalized_path,
            file_name,
            video.get('size', 0),
            video.get('title'),
            video.get('index_number'),
            video.get('duration'),
            video.get('start_time_in_ms'),
            video.get('end_time_in_ms'),
            last_modified,
            current_time,
            json.dumps(video.get('tags', [])),
            video.get('artist'),
            thumb_blob,
            thumb_mime,
            thumb_file,
            video.get('thumbnail_url'),
            video.get('description'),
            video.get('premiere_date'),
            video.get('user_rating'),
        )

        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            cursor.execute(
                '''
                    UPDATE videos
                    SET folder_id = ?,
                        series_id = ?,
                        season_id = ?,
                        media_id = ?,
                        file_name = ?,
                        file_size = ?,
                        title = ?,
                        index_number = ?,
                        duration = ?,
                        start_time_in_ms = ?,
                        end_time_in_ms = ?,
                        last_modified = ?,
                        cached_at = ?,
                        tags = ?,
                        artist = ?,
                        thumbnail = ?,
                        thumbnail_mime_type = ?,
                        thumbnail_file = ?,
                        thumbnail_url = ?,
                        description = ?,
                        premiere_date = ?,
                        user_rating = ?
                    WHERE file_path = ?
                ''',
                (
                    row[0], row[1], row[2], row[3],
                    row[5], row[6], row[7], row[8], row[9],
                    row[10], row[11], row[12], row[13], row[14],
                    row[15], row[16], row[17], row[18], row[19], row[20], row[21], row[22],
                    row[4],
                ),
            )

            if cursor.rowcount == 0:
                cursor.execute(
                    '''
                        INSERT INTO videos
                        (folder_id, series_id, season_id, media_id, file_path, file_name, file_size, title, index_number, duration,
                         start_time_in_ms, end_time_in_ms,
                         last_modified, cached_at, tags, artist, thumbnail, thumbnail_mime_type, thumbnail_file,
                         thumbnail_url, description, premiere_date, user_rating)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''',
                    row,
                )

            conn.commit()
        finally:
            conn.close()

    def delete_videos_not_in_paths(self, folder_id: int, existing_paths: set[str]) -> None:
        """Delete cached video rows for a folder that are not present anymore."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT file_path, thumbnail_file FROM videos WHERE folder_id = ?', (int(folder_id),))
            db_rows = cursor.fetchall()
            db_paths = {os.path.normpath(row[0]) for row in db_rows if row and row[0]}
            to_delete = db_paths - {os.path.normpath(p) for p in existing_paths}
            if not to_delete:
                return

            for file_path, thumbnail_file in db_rows:
                if not file_path:
                    continue
                if os.path.normpath(file_path) in to_delete:
                    self._delete_thumbnail_file(thumbnail_file)
            cursor.executemany(
                'DELETE FROM videos WHERE folder_id = ? AND file_path = ?',
                [(int(folder_id), p) for p in to_delete],
            )
            conn.commit()
        finally:
            conn.close()

    def get_video_series_id_map(self, folder_id: int) -> dict[str, int]:
        """Return mapping of series full_path -> series id for a folder."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, full_path FROM video_series WHERE folder_id = ?',
                (int(folder_id),),
            )
            out: dict[str, int] = {}
            for row in cursor.fetchall():
                if not row or not row[0] or not row[1]:
                    continue
                out[os.path.normpath(row[1])] = int(row[0])
            return out
        finally:
            conn.close()

    def get_video_season_id_map_for_folder(self, folder_id: int) -> dict[str, int]:
        """Return mapping of season full_path -> season id for all seasons in a folder."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                '''
                    SELECT vsn.id, vsn.full_path
                    FROM video_seasons vsn
                    JOIN video_series vs ON vs.id = vsn.series_id
                    WHERE vs.folder_id = ?
                ''',
                (int(folder_id),),
            )
            out: dict[str, int] = {}
            for row in cursor.fetchall():
                if not row or not row[0] or not row[1]:
                    continue
                out[os.path.normpath(row[1])] = int(row[0])
            return out
        finally:
            conn.close()

    def update_video_series_season_links(self, folder_id: int, file_path: str, *, series_id: int | None, season_id: int | None) -> None:
        """Update series_id/season_id for a specific video row."""
        if not isinstance(file_path, str) or not file_path:
            return
        normalized_path = os.path.normpath(file_path)
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE videos SET series_id = ?, season_id = ? WHERE folder_id = ? AND file_path = ?',
                (series_id, season_id, int(folder_id), normalized_path),
            )
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
        
        rows = []
        try:
            cursor.execute('''
                   SELECT v.media_id, v.file_path, v.file_name, v.file_size, v.title, v.index_number, v.duration,
                     v.start_time_in_ms, v.end_time_in_ms,
                                         v.last_modified, v.tags, v.artist, v.thumbnail, v.thumbnail_mime_type, v.thumbnail_file, v.thumbnail_url,
                     v.description, v.premiere_date, v.user_rating,
                                         vs.full_path AS series_full_path,
                                         vsea.full_path AS season_full_path
                FROM videos v
                LEFT JOIN video_series vs ON vs.id = v.series_id
                LEFT JOIN video_seasons vsea ON vsea.id = v.season_id
                WHERE v.folder_id = ?
                ORDER BY v.title, v.file_name
            ''', (folder_id,))
            rows = cursor.fetchall()
        except sqlite3.OperationalError:
            # Backward compatibility if the DB lacks the new columns/tables.
            cursor.execute('''
                   SELECT media_id, file_path, file_name, file_size, title, index_number, duration,
                     start_time_in_ms, end_time_in_ms,
                                         last_modified, tags, artist, thumbnail, thumbnail_mime_type, thumbnail_file, thumbnail_url,
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
            series_full_path = None
            season_full_path = None
            thumb_file = None

            # Handle multiple schema variants (older DBs may not have thumbnail_file or series tables).
            if len(row) >= 21:
                thumb_file = row[14]
                thumbnail_url = row[15]
                description = row[16]
                premiere_date = row[17]
                user_rating = row[18]
                series_full_path = row[19]
                season_full_path = row[20]
            elif len(row) >= 19:
                thumb_file = row[14]
                thumbnail_url = row[15]
                description = row[16]
                premiere_date = row[17]
                user_rating = row[18]
            else:
                thumbnail_url = row[14] if len(row) > 14 else None
                description = row[15] if len(row) > 15 else None
                premiere_date = row[16] if len(row) > 16 else None
                user_rating = row[17] if len(row) > 17 else None

            video = {
                'media_id': row[0],
                'path': row[1],
                'name': row[2],
                'size': row[3],
                'title': row[4] or os.path.splitext(row[2])[0],
                'index_number': row[5],
                'duration': row[6],
                'start_time_in_ms': row[7],
                'end_time_in_ms': row[8],
                'modified': row[9],
                'tags': json.loads(row[10]) if row[10] else [],
                'artist': row[11],
                'has_thumbnail': (row[12] is not None) or (thumb_file is not None),
                'thumbnail_url': thumbnail_url,
                'description': description,
                'premiere_date': premiere_date,
                'user_rating': user_rating,
            }

            # Preserve the folder-name semantics for series/season.
            # (The hierarchical /series endpoint provides the display titles.)
            if isinstance(series_full_path, str) and series_full_path.strip():
                video['series'] = os.path.basename(series_full_path.strip())
            if isinstance(season_full_path, str) and season_full_path.strip():
                video['season'] = os.path.basename(season_full_path.strip())
            videos.append(video)
        
        return videos

    def cache_video_series_tree(self, folder_id: int, series_tree: list[dict]):
        """Persist Series/Season rows for a folder without rewriting the videos table.

        This is useful for upgrades/backfills when videos are already cached but
        `video_series` / `video_seasons` are empty.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            cursor.execute(
                'SELECT recursive FROM video_folders WHERE id = ?',
                (folder_id,),
            )
            folder_row = cursor.fetchone()
            folder_recursive = bool(int(folder_row[0])) if folder_row and folder_row[0] is not None else False

            if not folder_recursive or not isinstance(series_tree, list):
                return

            cursor.execute(
                'DELETE FROM video_series WHERE folder_id = ?',
                (folder_id,),
            )

            # video_seasons rows are deleted via ON DELETE CASCADE on video_series.
            for series in series_tree:
                if not isinstance(series, dict):
                    continue
                full_path = series.get('full_path')
                if not isinstance(full_path, str) or not full_path:
                    continue

                title = series.get('title') if isinstance(series.get('title'), str) else None
                user_rating = series.get('user_rating') if isinstance(series.get('user_rating'), (int, float)) else None
                tags = series.get('tags') if isinstance(series.get('tags'), list) else []
                artists = series.get('artists') if isinstance(series.get('artists'), list) else []
                cover = series.get('cover') if isinstance(series.get('cover'), str) else None

                cursor.execute(
                    '''
                        INSERT INTO video_series (folder_id, full_path, title, user_rating, tags, artists, cover)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        folder_id,
                        os.path.normpath(full_path),
                        title,
                        float(user_rating) if isinstance(user_rating, (int, float)) else None,
                        json.dumps(tags),
                        json.dumps(artists),
                        cover,
                    ),
                )
                series_db_id = int(cursor.lastrowid)

                seasons = series.get('seasons')
                if isinstance(seasons, list):
                    for season in seasons:
                        if not isinstance(season, dict):
                            continue
                        season_full_path = season.get('full_path')
                        if not isinstance(season_full_path, str) or not season_full_path:
                            continue
                        season_title = season.get('title') if isinstance(season.get('title'), str) else None
                        season_user_rating = season.get('user_rating') if isinstance(season.get('user_rating'), (int, float)) else None
                        season_tags = season.get('tags') if isinstance(season.get('tags'), list) else []
                        season_artists = season.get('artists') if isinstance(season.get('artists'), list) else []
                        season_cover = season.get('cover') if isinstance(season.get('cover'), str) else None
                        season_index = season.get('index_number') if isinstance(season.get('index_number'), int) else None

                        cursor.execute(
                            '''
                                INSERT INTO video_seasons (series_id, full_path, title, user_rating, tags, artists, cover, index_number)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ''',
                            (
                                series_db_id,
                                os.path.normpath(season_full_path),
                                season_title,
                                float(season_user_rating) if isinstance(season_user_rating, (int, float)) else None,
                                json.dumps(season_tags),
                                json.dumps(season_artists),
                                season_cover,
                                season_index,
                            ),
                        )

            conn.commit()
        finally:
            conn.close()

    def get_cached_video_series_tree(self, folder_id):
        """Return a cached Series -> Seasons -> Videos structure for a folder.

        Returns:
            - list[dict] when cache is valid
            - [] when cache is valid but no series rows exist
            - None when cache is invalid or DB doesn't support the schema
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT last_scan FROM video_folders WHERE id = ?', (folder_id,))
        folder = cursor.fetchone()
        if not folder or folder[0] is None:
            conn.close()
            return None

        try:
            def _stable_tree_id(prefix: str, full_path: str | None) -> str:
                normalized = os.path.normpath(full_path or '')
                digest = hashlib.sha1(normalized.lower().encode('utf-8', errors='ignore')).hexdigest()[:12]
                return f"{prefix}_{digest}"

            cursor.execute('''
                SELECT id, full_path, title, user_rating, tags, artists, cover
                FROM video_series
                WHERE folder_id = ?
                ORDER BY COALESCE(title, full_path)
            ''', (folder_id,))
            series_rows = cursor.fetchall()

            series_by_id: dict[int, dict] = {}
            seasons_by_id: dict[int, dict] = {}

            for row in series_rows:
                sid = int(row[0])
                series_by_id[sid] = {
                    'id': _stable_tree_id('ser', row[1]),
                    'full_path': row[1],
                    'title': row[2] or (os.path.basename(row[1]) if row[1] else 'Untitled'),
                    'user_rating': row[3],
                    'tags': json.loads(row[4]) if row[4] else [],
                    'artists': json.loads(row[5]) if row[5] else [],
                    'cover': row[6],
                    'seasons': [],
                    'videos': [],
                }

            if series_by_id:
                placeholders = ','.join(['?'] * len(series_by_id))
                cursor.execute(
                    f'''
                        SELECT id, series_id, full_path, title, user_rating, tags, artists, cover, index_number
                        FROM video_seasons
                        WHERE series_id IN ({placeholders})
                        ORDER BY COALESCE(index_number, 999999), COALESCE(title, full_path)
                    ''',
                    tuple(series_by_id.keys()),
                )
                season_rows = cursor.fetchall()
                for row in season_rows:
                    season_id = int(row[0])
                    series_id = int(row[1])
                    season_dict = {
                        'id': _stable_tree_id('sea', row[2]),
                        'full_path': row[2],
                        'title': row[3] or (os.path.basename(row[2]) if row[2] else 'Untitled'),
                        'user_rating': row[4],
                        'tags': json.loads(row[5]) if row[5] else [],
                        'artists': json.loads(row[6]) if row[6] else [],
                        'cover': row[7],
                        'index_number': row[8],
                        'videos': [],
                    }
                    seasons_by_id[season_id] = season_dict
                    parent = series_by_id.get(series_id)
                    if parent is not None:
                        parent['seasons'].append(season_dict)

            cursor.execute('''
                SELECT folder_id, series_id, season_id, media_id, file_path, file_name, file_size, title,
                       index_number, duration, start_time_in_ms, end_time_in_ms, last_modified, tags, artist,
                       thumbnail, thumbnail_mime_type, thumbnail_file, thumbnail_url, description, premiere_date, user_rating
                FROM videos
                WHERE folder_id = ?
                ORDER BY COALESCE(series_id, 0), COALESCE(season_id, 0), COALESCE(index_number, 999999), COALESCE(title, file_name)
            ''', (folder_id,))
            video_rows = cursor.fetchall()

            for row in video_rows:
                v_series_id = row[1]
                v_season_id = row[2]
                video = {
                    'media_id': row[3],
                    'path': row[4],
                    'name': row[5],
                    'size': row[6],
                    'title': row[7] or os.path.splitext(row[5])[0],
                    'index_number': row[8],
                    'duration': row[9],
                    'start_time_in_ms': row[10],
                    'end_time_in_ms': row[11],
                    'modified': row[12],
                    'tags': json.loads(row[13]) if row[13] else [],
                    'artist': row[14],
                    'has_thumbnail': (row[15] is not None) or (row[17] is not None),
                    'thumbnail_url': row[18],
                    'description': row[19],
                    'premiere_date': row[20],
                    'user_rating': row[21],
                }

                if isinstance(v_season_id, int) and v_season_id in seasons_by_id:
                    seasons_by_id[v_season_id]['videos'].append(video)
                elif isinstance(v_series_id, int) and v_series_id in series_by_id:
                    series_by_id[v_series_id]['videos'].append(video)

            conn.close()
            return list(series_by_id.values())

        except sqlite3.OperationalError:
            conn.close()
            return None
    
    def get_video_thumbnail(self, file_path):
        """Get thumbnail data for a specific video by file path
        
        Returns:
            Tuple of (thumbnail_data, mime_type) or (None, None) if not found
        """
        normalized_path = os.path.normpath(file_path)
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                'SELECT thumbnail, thumbnail_mime_type, thumbnail_file FROM videos WHERE file_path = ?',
                (normalized_path,),
            )
            result = cursor.fetchone()
        except sqlite3.OperationalError:
            cursor.execute(
                'SELECT thumbnail, thumbnail_mime_type FROM videos WHERE file_path = ?',
                (normalized_path,),
            )
            result = cursor.fetchone()
        conn.close()

        if not result:
            return None, None

        thumbnail_blob = result[0] if len(result) > 0 else None
        mime_type = result[1] if len(result) > 1 else None
        thumbnail_file = result[2] if len(result) > 2 else None

        if thumbnail_blob:
            if isinstance(thumbnail_blob, memoryview):
                thumbnail_blob = thumbnail_blob.tobytes()
            if isinstance(thumbnail_blob, (bytes, bytearray)):
                return bytes(thumbnail_blob), mime_type

        if thumbnail_file:
            data = self._read_thumbnail_file(thumbnail_file)
            if isinstance(data, (bytes, bytearray)) and data:
                return bytes(data), mime_type

        return None, None

    def get_video_thumbnail_by_media_id(self, media_id: str):
        """Get thumbnail data for a specific video by its stable media_id.

        Returns:
            Tuple of (thumbnail_data, mime_type) or (None, None) if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                'SELECT thumbnail, thumbnail_mime_type, thumbnail_file FROM videos WHERE media_id = ?',
                (media_id,),
            )
            result = cursor.fetchone()
        except sqlite3.OperationalError:
            cursor.execute(
                'SELECT thumbnail, thumbnail_mime_type FROM videos WHERE media_id = ?',
                (media_id,),
            )
            result = cursor.fetchone()
        conn.close()

        if not result:
            return None, None

        thumbnail_blob = result[0] if len(result) > 0 else None
        mime_type = result[1] if len(result) > 1 else None
        thumbnail_file = result[2] if len(result) > 2 else None

        if thumbnail_blob:
            if isinstance(thumbnail_blob, memoryview):
                thumbnail_blob = thumbnail_blob.tobytes()
            if isinstance(thumbnail_blob, (bytes, bytearray)):
                return bytes(thumbnail_blob), mime_type

        if thumbnail_file:
            data = self._read_thumbnail_file(thumbnail_file)
            if isinstance(data, (bytes, bytearray)) and data:
                return bytes(data), mime_type

        return None, None

    def get_video_file_path_by_media_id(self, media_id: str):
        """Resolve a video's file path by its stable media_id.

        Returns:
            Normalized file path string, or None if not found.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT file_path FROM videos WHERE media_id = ?', (media_id,))
        row = cursor.fetchone()
        conn.close()
        if not row or not row[0]:
            return None
        return os.path.normpath(row[0])

    def update_video_user_metadata_by_media_id(self, media_id: str, *, user_rating, tags) -> bool:
        """Update user-editable metadata (tags + user_rating) for a cached video.

        Also updates cached_at so the cache is considered fresh against NFO changes.
        Returns True if a row was updated.
        """
        if not isinstance(media_id, str) or not media_id:
            return False

        # Normalize inputs
        rating = None
        try:
            if user_rating is None or user_rating == '':
                rating = None
            else:
                rating = float(user_rating)
                if rating < 0:
                    rating = 0.0
                if rating > 10:
                    rating = 10.0
        except Exception:
            rating = None

        tag_list: list[str] = []
        if isinstance(tags, (list, tuple)):
            for t in tags:
                if not isinstance(t, str):
                    continue
                tt = t.strip()
                if not tt:
                    continue
                if tt.lower() in {x.lower() for x in tag_list}:
                    continue
                tag_list.append(tt)
        elif isinstance(tags, str):
            # allow comma-separated string
            parts = [p.strip() for p in tags.split(',')]
            for p in parts:
                if p and p.lower() not in {x.lower() for x in tag_list}:
                    tag_list.append(p)

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE videos SET tags = ?, user_rating = ?, cached_at = ? WHERE media_id = ?',
                (json.dumps(tag_list), rating, datetime.now().timestamp(), media_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def get_videos_by_media_ids(self, media_ids):
        """Fetch minimal video info for a set of media_ids.

        Returns:
            Dict mapping media_id -> {'path': str, 'title': str, 'name': str}
        """
        if not media_ids:
            return {}

        unique_ids = []
        seen = set()
        for mid in media_ids:
            if not isinstance(mid, str) or not mid:
                continue
            if mid in seen:
                continue
            seen.add(mid)
            unique_ids.append(mid)
        if not unique_ids:
            return {}

        placeholders = ','.join(['?'] * len(unique_ids))
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            f'SELECT media_id, file_path, title, file_name FROM videos WHERE media_id IN ({placeholders})',
            tuple(unique_ids),
        )
        rows = cursor.fetchall()
        conn.close()

        results = {}
        for media_id, file_path, title, file_name in rows:
            results[media_id] = {
                'path': os.path.normpath(file_path) if file_path else None,
                'title': title,
                'name': file_name,
            }
        return results

    def get_videos_by_paths(self, file_paths):
        """Fetch cached video info for a set of file paths.

        Args:
            file_paths: Iterable of file path strings.

        Returns:
            Dict mapping normalized file_path -> video dict containing cached metadata.
        """
        if not file_paths:
            return {}

        unique_paths: list[str] = []
        seen: set[str] = set()
        for p in file_paths:
            if not isinstance(p, str) or not p:
                continue
            norm = os.path.normpath(p)
            if norm in seen:
                continue
            seen.add(norm)
            unique_paths.append(norm)

        if not unique_paths:
            return {}

        placeholders = ','.join(['?'] * len(unique_paths))
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                f'''SELECT media_id, file_path, file_name, title, duration,
                          start_time_in_ms, end_time_in_ms, tags, artist,
                          thumbnail, thumbnail_file, thumbnail_url
                     FROM videos
                    WHERE file_path IN ({placeholders})''',
                tuple(unique_paths),
            )
            rows = cursor.fetchall()
        finally:
            conn.close()

        results: dict[str, dict] = {}
        for (media_id, file_path, file_name, title, duration,
             start_ms, end_ms, tags_json, artist,
             thumb_blob, thumb_file, thumb_url) in rows:
            norm = os.path.normpath(file_path) if file_path else None
            if not norm:
                continue
            results[norm] = {
                'media_id': media_id,
                'path': norm,
                'name': file_name,
                'title': title,
                'duration': duration,
                'start_time_in_ms': start_ms,
                'end_time_in_ms': end_ms,
                'tags': json.loads(tags_json) if tags_json else [],
                'artist': artist,
                'has_thumbnail': (thumb_blob is not None) or (thumb_file is not None) or (thumb_url is not None),
                'thumbnail_url': thumb_url,
            }

        return results
    
    def invalidate_video_folder(self, folder_id):
        """Invalidate cache for a specific video folder"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            'SELECT thumbnail_file FROM videos WHERE folder_id = ?',
            (folder_id,),
        )
        for (thumbnail_file,) in cursor.fetchall() or []:
            self._delete_thumbnail_file(thumbnail_file)
        
        cursor.execute(
            'DELETE FROM videos WHERE folder_id = ?',
            (folder_id,)
        )
        cursor.execute(
            'DELETE FROM video_series WHERE folder_id = ?',
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
        cursor.execute('DELETE FROM video_seasons')
        cursor.execute('DELETE FROM video_series')
        cursor.execute('DELETE FROM video_folders')
        
        conn.commit()
        conn.close()

        try:
            shutil.rmtree(self._get_thumbs_root_dir(), ignore_errors=True)
        except Exception:
            pass
    
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
            SELECT id, username, password_hash, role, preferred_language, created_at
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
                'preferred_language': row[4],
                'created_at': row[5]
            }
        return None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, password_hash, role, preferred_language, created_at
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
                'preferred_language': row[4],
                'created_at': row[5]
            }
        return None
    
    def get_all_users(self):
        """Get all users"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, role, preferred_language, created_at
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
                'preferred_language': row[3],
                'created_at': row[4]
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

    def update_user_preferred_language(self, user_id, preferred_language: str):
        """Update the preferred language for a user."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE users
            SET preferred_language = ?
            WHERE id = ?
        ''', (preferred_language, user_id))

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
