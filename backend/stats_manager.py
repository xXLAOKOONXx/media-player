"""
Stats Manager
Manages media playback statistics in a separate database
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger('StatsManager')


class StatsManager:
    """Manages media playback statistics in a separate database"""
    
    def __init__(self, stats_folder=None):
        self.stats_folder = stats_folder
        self.db_path = None
        self._initialized = False
        
        if stats_folder:
            self._initialize_database(stats_folder)
    
    def _initialize_database(self, stats_folder):
        """Initialize the stats database in the specified folder"""
        try:
            # Create folder if it doesn't exist
            os.makedirs(stats_folder, exist_ok=True)
            
            # Set database path
            self.db_path = os.path.join(stats_folder, 'media-player-stats.db')
            
            # Create the database
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            cursor = conn.cursor()
            
            # Create stats table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS media_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    folder_path TEXT NOT NULL,
                    username TEXT NOT NULL
                )
            ''')
            
            # Create indexes for faster lookups
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_media_stats_timestamp ON media_stats (timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_media_stats_username ON media_stats (username)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_media_stats_folder ON media_stats (folder_path)')
            
            conn.commit()
            conn.close()
            
            self._initialized = True
            logger.info(f"Stats database initialized at {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize stats database: {e}")
            self._initialized = False
    
    def set_stats_folder(self, stats_folder):
        """Set the stats folder and reinitialize database"""
        self.stats_folder = stats_folder
        if stats_folder:
            self._initialize_database(stats_folder)
        else:
            self._initialized = False
            self.db_path = None
    
    def record_media_stat(self, folder_path, username):
        """Record a media playback stat entry
        
        Args:
            folder_path: Absolute path to the folder containing the media file
            username: Username of the user playing the media
        
        Returns:
            True if successful, False otherwise
        """
        if not self._initialized or not self.db_path:
            logger.warning("Stats database not initialized, cannot record stat")
            return False
        
        try:
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            cursor = conn.cursor()
            
            current_time = datetime.now().timestamp()
            
            cursor.execute('''
                INSERT INTO media_stats (timestamp, folder_path, username)
                VALUES (?, ?, ?)
            ''', (current_time, folder_path, username))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Recorded stat: folder={folder_path}, user={username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record stat: {e}")
            return False
    
    def get_media_stats(self, username=None, start_time=None, end_time=None, limit=None):
        """Get media stats with optional filters
        
        Args:
            username: Filter by username (optional)
            start_time: Filter by start timestamp (optional)
            end_time: Filter by end timestamp (optional)
            limit: Limit number of results (optional)
        
        Returns:
            List of stat entries, or empty list if not initialized
        """
        if not self._initialized or not self.db_path:
            logger.warning("Stats database not initialized, cannot retrieve stats")
            return []
        
        try:
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            cursor = conn.cursor()
            
            query = 'SELECT id, timestamp, folder_path, username FROM media_stats WHERE 1=1'
            params = []
            
            if username:
                query += ' AND username = ?'
                params.append(username)
            
            if start_time:
                query += ' AND timestamp >= ?'
                params.append(start_time)
            
            if end_time:
                query += ' AND timestamp <= ?'
                params.append(end_time)
            
            query += ' ORDER BY timestamp DESC'
            
            if limit:
                query += ' LIMIT ?'
                params.append(limit)
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            conn.close()
            
            stats = []
            for row in results:
                stats.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'folder_path': row[2],
                    'username': row[3]
                })
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to retrieve stats: {e}")
            return []
    
    def is_initialized(self):
        """Check if the stats database is initialized and ready"""
        return self._initialized
