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
            
            # Create the database / open existing
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            cursor = conn.cursor()

            # If the table doesn't exist yet, create it using the new schema.
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='media_stats'")
            has_table = cursor.fetchone() is not None

            if not has_table:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS media_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp REAL NOT NULL,
                        file_path TEXT NOT NULL,
                        username TEXT NOT NULL
                    )
                ''')

            # Create indexes for faster lookups (compatible with both schemas)
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_media_stats_timestamp ON media_stats (timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_media_stats_username ON media_stats (username)')

            # Legacy DBs from earlier versions used folder_path; newer DBs use file_path.
            cursor.execute('PRAGMA table_info(media_stats)')
            columns = {row[1] for row in cursor.fetchall()}
            if 'file_path' in columns:
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_media_stats_file ON media_stats (file_path)')
            elif 'folder_path' in columns:
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
    
    def _get_path_column_name(self):
        """Determine whether the DB uses 'file_path' or legacy 'folder_path' column"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            cursor = conn.cursor()
            cursor.execute('PRAGMA table_info(media_stats)')
            columns = [row[1] for row in cursor.fetchall()]
            conn.close()
            if 'file_path' in columns:
                return 'file_path'
            elif 'folder_path' in columns:
                return 'folder_path'
        except Exception:
            pass
        # Default to new schema
        return 'file_path'

    def record_media_stat(self, file_path, username):
        """Record a media playback stat entry
        
        Args:
            file_path: Absolute path to the media file
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
            col = self._get_path_column_name()
            
            if col not in ('file_path', 'folder_path'):
                raise ValueError(f"Unexpected stats column: {col}")

            query = f"INSERT INTO media_stats (timestamp, {col}, username) VALUES (?, ?, ?)"
            cursor.execute(query, (current_time, file_path, username))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Recorded stat: path={file_path}, user={username}")
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
            
            col = self._get_path_column_name()
            query = f'SELECT id, timestamp, {col}, username FROM media_stats WHERE 1=1'
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
                    'file_path': row[2],
                    'username': row[3]
                })
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to retrieve stats: {e}")
            return []
    
    def is_initialized(self):
        """Check if the stats database is initialized and ready"""
        return self._initialized
