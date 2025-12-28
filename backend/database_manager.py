"""
Unified Database Manager
Manages a single SQLite database for all media player data including:
- Configuration (device-specific)
- Music cache (folders and tracks)
- Video cache (folders and videos)
"""

import sqlite3
import json
import platform
from datetime import datetime
from pathlib import Path


class DatabaseManager:
    """Manages unified SQLite database for all media player data"""
    
    def __init__(self, db_path='media_player.db'):
        self.db_path = db_path
        self.device_name = platform.node()  # Get computer hostname
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with all required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Configuration table (device-specific)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_name TEXT NOT NULL,
                config_key TEXT NOT NULL,
                config_value TEXT NOT NULL,
                updated_at REAL NOT NULL,
                UNIQUE(device_name, config_key)
            )
        ''')
        
        # Music folders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS music_folders (
                id INTEGER PRIMARY KEY,
                device_name TEXT NOT NULL,
                path TEXT NOT NULL,
                recursive INTEGER NOT NULL,
                last_scan REAL,
                UNIQUE(device_name, id)
            )
        ''')
        
        # Music tracks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS music_tracks (
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
                FOREIGN KEY (folder_id) REFERENCES music_folders (id) ON DELETE CASCADE,
                UNIQUE(device_name, folder_id, file_path)
            )
        ''')
        
        # Video folders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_folders (
                id INTEGER PRIMARY KEY,
                device_name TEXT NOT NULL,
                path TEXT NOT NULL,
                recursive INTEGER NOT NULL,
                last_scan REAL,
                UNIQUE(device_name, id)
            )
        ''')
        
        # Video files table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
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
                FOREIGN KEY (folder_id) REFERENCES video_folders (id) ON DELETE CASCADE,
                UNIQUE(device_name, folder_id, file_path)
            )
        ''')
        
        # Create indexes for faster lookups
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_config_device ON config (device_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_music_folder_device ON music_folders (device_name, id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_music_tracks_folder ON music_tracks (device_name, folder_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_music_tracks_path ON music_tracks (device_name, file_path)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_video_folder_device ON video_folders (device_name, id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_folder ON videos (device_name, folder_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_path ON videos (device_name, file_path)')
        
        conn.commit()
        conn.close()
    
    # Configuration methods
    def get_config(self, key, default=None):
        """Get configuration value for this device"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT config_value FROM config WHERE device_name = ? AND config_key = ?',
            (self.device_name, key)
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
        """Set configuration value for this device"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        value_str = json.dumps(value) if not isinstance(value, str) else value
        current_time = datetime.now().timestamp()
        
        cursor.execute('''
            INSERT INTO config (device_name, config_key, config_value, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(device_name, config_key) 
            DO UPDATE SET config_value = ?, updated_at = ?
        ''', (self.device_name, key, value_str, current_time, value_str, current_time))
        
        conn.commit()
        conn.close()
    
    def get_all_config(self):
        """Get all configuration for this device"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT config_key, config_value FROM config WHERE device_name = ?',
            (self.device_name,)
        )
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        recursive_int = 1 if recursive else 0
        
        cursor.execute(
            'SELECT path, recursive FROM music_folders WHERE device_name = ? AND id = ?',
            (self.device_name, folder_id)
        )
        existing = cursor.fetchone()
        
        if existing is None:
            cursor.execute('''
                INSERT INTO music_folders (device_name, id, path, recursive, last_scan)
                VALUES (?, ?, ?, ?, NULL)
            ''', (self.device_name, folder_id, path, recursive_int))
        else:
            existing_path, existing_recursive = existing[0], existing[1]
            
            if existing_path != path or int(existing_recursive) != recursive_int:
                cursor.execute(
                    'DELETE FROM music_tracks WHERE device_name = ? AND folder_id = ?',
                    (self.device_name, folder_id)
                )
                cursor.execute(
                    'UPDATE music_folders SET last_scan = NULL WHERE device_name = ? AND id = ?',
                    (self.device_name, folder_id)
                )
            
            cursor.execute(
                'UPDATE music_folders SET path = ?, recursive = ? WHERE device_name = ? AND id = ?',
                (path, recursive_int, self.device_name, folder_id)
            )
        
        conn.commit()
        conn.close()
    
    def cache_music_tracks(self, folder_id, tracks):
        """Cache music track metadata for a folder"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE music_folders SET last_scan = ? WHERE device_name = ? AND id = ?',
            (datetime.now().timestamp(), self.device_name, folder_id)
        )
        
        cursor.execute(
            'DELETE FROM music_tracks WHERE device_name = ? AND folder_id = ?',
            (self.device_name, folder_id)
        )
        
        current_time = datetime.now().timestamp()
        rows = []
        for track in tracks:
            last_modified = track.get('last_modified')
            rows.append((
                self.device_name,
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
            (device_name, folder_id, file_path, file_name, file_size, artist, title, album,
             duration, tags, last_modified, cached_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', rows)
        
        conn.commit()
        conn.close()
    
    def get_cached_music_tracks(self, folder_id):
        """Retrieve cached music tracks for a folder"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT last_scan FROM music_folders WHERE device_name = ? AND id = ?',
            (self.device_name, folder_id)
        )
        folder = cursor.fetchone()
        
        if not folder or folder[0] is None:
            conn.close()
            return None
        
        cursor.execute('''
            SELECT file_path, file_name, file_size, artist, title, album,
                   duration, tags, last_modified
            FROM music_tracks
            WHERE device_name = ? AND folder_id = ?
            ORDER BY artist, title
        ''', (self.device_name, folder_id))
        
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'DELETE FROM music_tracks WHERE device_name = ? AND folder_id = ?',
            (self.device_name, folder_id)
        )
        cursor.execute(
            'UPDATE music_folders SET last_scan = NULL WHERE device_name = ? AND id = ?',
            (self.device_name, folder_id)
        )
        
        conn.commit()
        conn.close()
    
    def update_music_track_duration(self, file_path, duration):
        """Update cached duration for a single music track"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE music_tracks SET duration = ? WHERE device_name = ? AND file_path = ?',
            (duration, self.device_name, file_path)
        )
        
        conn.commit()
        conn.close()
    
    def get_music_cache_stats(self):
        """Get music cache statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT COUNT(*) FROM music_folders WHERE device_name = ?',
            (self.device_name,)
        )
        folder_count = cursor.fetchone()[0]
        
        cursor.execute(
            'SELECT COUNT(*) FROM music_tracks WHERE device_name = ?',
            (self.device_name,)
        )
        track_count = cursor.fetchone()[0]
        
        cursor.execute(
            'SELECT SUM(file_size) FROM music_tracks WHERE device_name = ?',
            (self.device_name,)
        )
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        recursive_int = 1 if recursive else 0
        
        cursor.execute(
            'SELECT path, recursive FROM video_folders WHERE device_name = ? AND id = ?',
            (self.device_name, folder_id)
        )
        existing = cursor.fetchone()
        
        if existing is None:
            cursor.execute('''
                INSERT INTO video_folders (device_name, id, path, recursive, last_scan)
                VALUES (?, ?, ?, ?, NULL)
            ''', (self.device_name, folder_id, path, recursive_int))
        else:
            existing_path, existing_recursive = existing[0], existing[1]
            
            if existing_path != path or int(existing_recursive) != recursive_int:
                cursor.execute(
                    'DELETE FROM videos WHERE device_name = ? AND folder_id = ?',
                    (self.device_name, folder_id)
                )
                cursor.execute(
                    'UPDATE video_folders SET last_scan = NULL WHERE device_name = ? AND id = ?',
                    (self.device_name, folder_id)
                )
            
            cursor.execute(
                'UPDATE video_folders SET path = ?, recursive = ? WHERE device_name = ? AND id = ?',
                (path, recursive_int, self.device_name, folder_id)
            )
        
        conn.commit()
        conn.close()
    
    def cache_videos(self, folder_id, videos):
        """Cache video metadata for a folder"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE video_folders SET last_scan = ? WHERE device_name = ? AND id = ?',
            (datetime.now().timestamp(), self.device_name, folder_id)
        )
        
        cursor.execute(
            'DELETE FROM videos WHERE device_name = ? AND folder_id = ?',
            (self.device_name, folder_id)
        )
        
        current_time = datetime.now().timestamp()
        rows = []
        for video in videos:
            last_modified = video.get('modified') or video.get('last_modified')
            rows.append((
                self.device_name,
                folder_id,
                video['path'],
                video['name'],
                video.get('size', 0),
                video.get('title'),
                video.get('duration'),
                last_modified,
                current_time,
            ))
        
        cursor.executemany('''
            INSERT INTO videos
            (device_name, folder_id, file_path, file_name, file_size, title, duration,
             last_modified, cached_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', rows)
        
        conn.commit()
        conn.close()
    
    def get_cached_videos(self, folder_id):
        """Retrieve cached videos for a folder"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT last_scan FROM video_folders WHERE device_name = ? AND id = ?',
            (self.device_name, folder_id)
        )
        folder = cursor.fetchone()
        
        if not folder or folder[0] is None:
            conn.close()
            return None
        
        cursor.execute('''
            SELECT file_path, file_name, file_size, title, duration, last_modified
            FROM videos
            WHERE device_name = ? AND folder_id = ?
            ORDER BY title, file_name
        ''', (self.device_name, folder_id))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return []
        
        videos = []
        for row in rows:
            import os
            video = {
                'path': row[0],
                'name': row[1],
                'size': row[2],
                'title': row[3] or os.path.splitext(row[1])[0],
                'duration': row[4],
                'modified': row[5]
            }
            videos.append(video)
        
        return videos
    
    def invalidate_video_folder(self, folder_id):
        """Invalidate cache for a specific video folder"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'DELETE FROM videos WHERE device_name = ? AND folder_id = ?',
            (self.device_name, folder_id)
        )
        cursor.execute(
            'UPDATE video_folders SET last_scan = NULL WHERE device_name = ? AND id = ?',
            (self.device_name, folder_id)
        )
        
        conn.commit()
        conn.close()
    
    def update_video_duration(self, file_path, duration):
        """Update cached duration for a single video"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE videos SET duration = ? WHERE device_name = ? AND file_path = ?',
            (duration, self.device_name, file_path)
        )
        
        conn.commit()
        conn.close()
    
    def get_video_cache_stats(self):
        """Get video cache statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT COUNT(*) FROM video_folders WHERE device_name = ?',
            (self.device_name,)
        )
        folder_count = cursor.fetchone()[0]
        
        cursor.execute(
            'SELECT COUNT(*) FROM videos WHERE device_name = ?',
            (self.device_name,)
        )
        video_count = cursor.fetchone()[0]
        
        cursor.execute(
            'SELECT SUM(file_size) FROM videos WHERE device_name = ?',
            (self.device_name,)
        )
        total_size = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'folders': folder_count,
            'videos': video_count,
            'total_size_bytes': total_size
        }
    
    def clear_all_cache(self):
        """Clear all cached data for this device"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM music_tracks WHERE device_name = ?', (self.device_name,))
        cursor.execute('DELETE FROM music_folders WHERE device_name = ?', (self.device_name,))
        cursor.execute('DELETE FROM videos WHERE device_name = ?', (self.device_name,))
        cursor.execute('DELETE FROM video_folders WHERE device_name = ?', (self.device_name,))
        
        conn.commit()
        conn.close()
