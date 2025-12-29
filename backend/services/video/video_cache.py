"""
Video Cache Manager
Handles SQLite caching of video file metadata for faster loading
"""

import sqlite3
import os
import json
from pathlib import Path
from datetime import datetime

from services.general.database_manager import DatabaseManager


class VideoCache:
    """Manages SQLite cache for video metadata"""
    
    def __init__(self, db_path=None):
        # Default to the unified app-data database path used across the backend.
        self.db = DatabaseManager(db_path)
    

    def register_folder(self, folder_id, path, recursive):
        """Register a video folder in the cache"""
        self.db.register_video_folder(folder_id, path, recursive)
    
    def cache_videos(self, folder_id, videos, series_tree=None):
        """Cache video metadata for a folder.

        If `series_tree` is provided, it will also be stored in the DB tables
        `video_series` and `video_seasons`.
        """
        # Ensure last_modified is set for all videos
        for video in videos:
            last_modified = video.get('modified') or video.get('last_modified')
            if last_modified is None:
                try:
                    last_modified = os.path.getmtime(video['path']) if os.path.exists(video['path']) else None
                except OSError:
                    last_modified = None
            video['last_modified'] = last_modified
        
        self.db.cache_videos(folder_id, videos, series_tree=series_tree)
    
    def get_cached_videos(self, folder_id):
        """Retrieve cached videos for a folder
        
        Returns:
            List of video dicts or None if cache is invalid
        """
        return self.db.get_cached_videos(folder_id)

    def get_cached_series_tree(self, folder_id):
        """Retrieve cached series tree for a folder, or None if cache invalid."""
        return self.db.get_cached_video_series_tree(folder_id)

    def cache_series_tree(self, folder_id, series_tree):
        """Cache Series/Season rows without rewriting videos."""
        self.db.cache_video_series_tree(folder_id, series_tree)

    def update_folder_last_scan(self, folder_id, timestamp=None):
        self.db.update_video_folder_last_scan(folder_id, timestamp)

    def get_video_cache_freshness(self, file_path: str):
        return self.db.get_video_cache_freshness(file_path)

    def get_cached_video_by_path(self, file_path: str):
        return self.db.get_cached_video_by_path(file_path)

    def upsert_video(self, folder_id: int, video: dict, *, series_id=None, season_id=None):
        self.db.upsert_video(folder_id, video, series_id=series_id, season_id=season_id)

    def delete_videos_not_in_paths(self, folder_id: int, existing_paths: set[str]):
        self.db.delete_videos_not_in_paths(folder_id, existing_paths)

    def get_video_series_id_map(self, folder_id: int):
        return self.db.get_video_series_id_map(folder_id)

    def get_video_season_id_map_for_folder(self, folder_id: int):
        return self.db.get_video_season_id_map_for_folder(folder_id)

    def update_video_series_season_links(self, folder_id: int, file_path: str, *, series_id=None, season_id=None):
        self.db.update_video_series_season_links(folder_id, file_path, series_id=series_id, season_id=season_id)
    
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
