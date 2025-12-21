"""
Music Cache Manager
Handles SQLite caching of audio file metadata for faster loading
"""

import sqlite3
import os
import json
from pathlib import Path
from datetime import datetime


class MusicCache:
    """Manages SQLite cache for music metadata"""
    
    def __init__(self, db_path='music_cache.db'):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tracks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tracks (
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
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_folder_id ON tracks (folder_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_path ON tracks (file_path)')
        
        conn.commit()
        conn.close()
    
    def register_folder(self, folder_id, path, recursive):
        """Register a music folder in the cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO folders (id, path, recursive, last_scan)
            VALUES (?, ?, ?, ?)
        ''', (folder_id, path, 1 if recursive else 0, None))
        
        conn.commit()
        conn.close()
    
    def cache_tracks(self, folder_id, tracks):
        """Cache track metadata for a folder"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update last scan time
        cursor.execute('UPDATE folders SET last_scan = ? WHERE id = ?', 
                      (datetime.now().timestamp(), folder_id))
        
        # Delete old tracks for this folder
        cursor.execute('DELETE FROM tracks WHERE folder_id = ?', (folder_id,))
        
        # Insert new tracks
        current_time = datetime.now().timestamp()
        for track in tracks:
            cursor.execute('''
                INSERT INTO tracks 
                (folder_id, file_path, file_name, file_size, artist, title, album, 
                 duration, tags, last_modified, cached_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                folder_id,
                track['path'],
                track['name'],
                track.get('size', 0),
                track.get('artist'),
                track.get('title'),
                track.get('album'),
                track.get('duration'),
                json.dumps(track.get('tags', [])),
                os.path.getmtime(track['path']) if os.path.exists(track['path']) else None,
                current_time
            ))
        
        conn.commit()
        conn.close()
    
    def get_cached_tracks(self, folder_id):
        """Retrieve cached tracks for a folder
        
        Returns:
            List of track dicts or None if cache is invalid
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if folder exists
        cursor.execute('SELECT last_scan FROM folders WHERE id = ?', (folder_id,))
        folder = cursor.fetchone()
        
        if not folder or folder[0] is None:
            conn.close()
            return None
        
        # Get cached tracks
        cursor.execute('''
            SELECT file_path, file_name, file_size, artist, title, album, 
                   duration, tags, last_modified
            FROM tracks 
            WHERE folder_id = ?
            ORDER BY artist, title
        ''', (folder_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return []
        
        tracks = []
        for row in rows:
            # Verify file still exists and hasn't been modified
            file_path = row[0]
            cached_mtime = row[8]
            
            if os.path.exists(file_path):
                current_mtime = os.path.getmtime(file_path)
                # If file modified, invalidate cache
                if cached_mtime and abs(current_mtime - cached_mtime) > 1:
                    return None
                
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
    
    def invalidate_folder(self, folder_id):
        """Invalidate cache for a specific folder"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM tracks WHERE folder_id = ?', (folder_id,))
        cursor.execute('UPDATE folders SET last_scan = NULL WHERE id = ?', (folder_id,))
        
        conn.commit()
        conn.close()
    
    def clear_cache(self):
        """Clear all cached data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM tracks')
        cursor.execute('DELETE FROM folders')
        
        conn.commit()
        conn.close()
    
    def get_cache_stats(self):
        """Get cache statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM folders')
        folder_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM tracks')
        track_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(file_size) FROM tracks')
        total_size = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'folders': folder_count,
            'tracks': track_count,
            'total_size_bytes': total_size
        }
