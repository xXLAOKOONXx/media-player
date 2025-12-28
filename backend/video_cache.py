"""
Video Cache Manager
Handles SQLite caching of video file metadata for faster loading
"""

import sqlite3
import os
import json
from pathlib import Path
from datetime import datetime


class VideoCache:
    """Manages SQLite cache for video metadata"""
    
    def __init__(self, db_path='video_cache.db'):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create videos table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder_id INTEGER NOT NULL,
                file_path TEXT NOT NULL UNIQUE,
                file_name TEXT NOT NULL,
                file_size INTEGER,
                title TEXT,
                duration REAL,
                last_modified REAL,
                cached_at REAL NOT NULL,
                FOREIGN KEY (folder_id) REFERENCES folders (id) ON DELETE CASCADE
            )
        ''')
        
        # Create folders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS folders (
                id INTEGER PRIMARY KEY,
                path TEXT NOT NULL UNIQUE,
                recursive INTEGER NOT NULL,
                last_scan REAL
            )
        ''')
        
        # Create index for faster lookups
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_folder_id ON videos (folder_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_path ON videos (file_path)')
        
        conn.commit()
        conn.close()
    
    def register_folder(self, folder_id, path, recursive):
        """Register a video folder in the cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        recursive_int = 1 if recursive else 0

        # Important: do NOT blindly REPLACE here.
        # REPLACE deletes + re-inserts the row, which would reset last_scan to NULL
        # on every request and effectively disable caching.
        cursor.execute('SELECT path, recursive FROM folders WHERE id = ?', (folder_id,))
        existing = cursor.fetchone()

        if existing is None:
            cursor.execute('''
                INSERT INTO folders (id, path, recursive, last_scan)
                VALUES (?, ?, ?, NULL)
            ''', (folder_id, path, recursive_int))
        else:
            existing_path, existing_recursive = existing[0], existing[1]

            # If folder definition changed, invalidate cached videos.
            if existing_path != path or int(existing_recursive) != recursive_int:
                cursor.execute('DELETE FROM videos WHERE folder_id = ?', (folder_id,))
                cursor.execute('UPDATE folders SET last_scan = NULL WHERE id = ?', (folder_id,))

            cursor.execute('UPDATE folders SET path = ?, recursive = ? WHERE id = ?',
                           (path, recursive_int, folder_id))
        
        conn.commit()
        conn.close()
    
    def cache_videos(self, folder_id, videos):
        """Cache video metadata for a folder"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update last scan time
        cursor.execute('UPDATE folders SET last_scan = ? WHERE id = ?', 
                      (datetime.now().timestamp(), folder_id))
        
        # Delete old videos for this folder
        cursor.execute('DELETE FROM videos WHERE folder_id = ?', (folder_id,))
        
        # Insert new videos
        current_time = datetime.now().timestamp()

        rows = []
        for video in videos:
            # Get modification time - prefer 'modified' key for consistency
            # Also check 'last_modified' for backwards compatibility
            last_modified = video.get('modified') or video.get('last_modified')
            if last_modified is None:
                try:
                    last_modified = os.path.getmtime(video['path']) if os.path.exists(video['path']) else None
                except OSError:
                    last_modified = None

            rows.append((
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
            (folder_id, file_path, file_name, file_size, title, duration, 
             last_modified, cached_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', rows)
        
        conn.commit()
        conn.close()
    
    def get_cached_videos(self, folder_id):
        """Retrieve cached videos for a folder
        
        Returns:
            List of video dicts or None if cache is invalid
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if folder exists
        cursor.execute('SELECT last_scan FROM folders WHERE id = ?', (folder_id,))
        folder = cursor.fetchone()
        
        if not folder or folder[0] is None:
            conn.close()
            return None
        
        # Get cached videos
        cursor.execute('''
            SELECT file_path, file_name, file_size, title, duration, last_modified
            FROM videos 
            WHERE folder_id = ?
            ORDER BY title, file_name
        ''', (folder_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return []
        
        # Trust the cache without checking file existence for performance.
        # This improves load times significantly, especially on network shares.
        # Trade-off: May return entries for deleted files until next refresh.
        # Files are validated when adding to playlists or on manual refresh.
        videos = []
        for row in rows:
            video = {
                'path': row[0],
                'name': row[1],
                'size': row[2],
                'title': row[3] or os.path.splitext(row[1])[0],  # Fallback to filename without extension
                'duration': row[4],
                'modified': row[5]
            }
            videos.append(video)
        
        return videos
    
    def invalidate_folder(self, folder_id):
        """Invalidate cache for a specific folder"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM videos WHERE folder_id = ?', (folder_id,))
        cursor.execute('UPDATE folders SET last_scan = NULL WHERE id = ?', (folder_id,))
        
        conn.commit()
        conn.close()
    
    def clear_cache(self):
        """Clear all cached data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM videos')
        cursor.execute('DELETE FROM folders')
        
        conn.commit()
        conn.close()
    
    def get_cache_stats(self):
        """Get cache statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM folders')
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

    def update_video_duration(self, file_path, duration):
        """Update cached duration for a single video by file path.

        This is used to backfill durations lazily (e.g., when a video is played).
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            'UPDATE videos SET duration = ? WHERE file_path = ?',
            (duration, file_path),
        )

        conn.commit()
        conn.close()
