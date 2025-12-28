"""
Video Cache Manager
Handles SQLite caching of video file metadata for faster loading
"""

import sqlite3
import os
import json
from pathlib import Path
from datetime import datetime

from database_manager import DatabaseManager


class VideoCache:
    """Manages SQLite cache for video metadata"""
    
    def __init__(self, db_path='media_player.db'):
        self.db = DatabaseManager(db_path)
    

    def register_folder(self, folder_id, path, recursive):
        """Register a video folder in the cache"""
        self.db.register_video_folder(folder_id, path, recursive)
    
    def cache_videos(self, folder_id, videos):
        """Cache video metadata for a folder"""
        # Ensure last_modified is set for all videos
        for video in videos:
            last_modified = video.get('modified') or video.get('last_modified')
            if last_modified is None:
                try:
                    last_modified = os.path.getmtime(video['path']) if os.path.exists(video['path']) else None
                except OSError:
                    last_modified = None
            video['last_modified'] = last_modified
        
        self.db.cache_videos(folder_id, videos)
    
    def get_cached_videos(self, folder_id):
        """Retrieve cached videos for a folder
        
        Returns:
            List of video dicts or None if cache is invalid
        """
        return self.db.get_cached_videos(folder_id)
    
    def invalidate_folder(self, folder_id):
        """Invalidate cache for a specific folder"""
        self.db.invalidate_video_folder(folder_id)
    
    def clear_cache(self):
        """Clear all cached data"""
        self.db.clear_all_cache()
    
    def get_cache_stats(self):
        """Get cache statistics"""
        return self.db.get_video_cache_stats()

    def update_video_duration(self, file_path, duration):
        """Update cached duration for a single video by file path.

        This is used to backfill durations lazily (e.g., when a video is played).
        """
        self.db.update_video_duration(file_path, duration)
