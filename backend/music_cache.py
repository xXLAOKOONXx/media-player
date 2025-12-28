"""
Music Cache Manager
Handles SQLite caching of audio file metadata for faster loading
"""

import sqlite3
import os
import json
from pathlib import Path
from datetime import datetime

from audio_metadata import display_title
from database_manager import DatabaseManager


class MusicCache:
    """Manages SQLite cache for music metadata"""
    
    def __init__(self, db_path='media_player.db'):
        self.db = DatabaseManager(db_path)
    

    def register_folder(self, folder_id, path, recursive):
        """Register a music folder in the cache"""
        self.db.register_music_folder(folder_id, path, recursive)
    
    def cache_tracks(self, folder_id, tracks):
        """Cache track metadata for a folder"""
        # Ensure last_modified is set for all tracks
        for track in tracks:
            if track.get('last_modified') is None:
                try:
                    track['last_modified'] = os.path.getmtime(track['path']) if os.path.exists(track['path']) else None
                except OSError:
                    track['last_modified'] = None
        
        self.db.cache_music_tracks(folder_id, tracks)
    
    def get_cached_tracks(self, folder_id):
        """Retrieve cached tracks for a folder
        
        Returns:
            List of track dicts or None if cache is invalid
        """
        tracks = self.db.get_cached_music_tracks(folder_id)
        
        if tracks is None:
            return None
        
        # Ensure consistent title fallback for all tracks
        for track in tracks:
            track['title'] = display_title(track)
        
        return tracks
    
    def invalidate_folder(self, folder_id):
        """Invalidate cache for a specific folder"""
        self.db.invalidate_music_folder(folder_id)
    
    def clear_cache(self):
        """Clear all cached data"""
        self.db.clear_all_cache()
    
    def get_cache_stats(self):
        """Get cache statistics"""
        return self.db.get_music_cache_stats()

    def update_track_duration(self, file_path, duration):
        """Update cached duration for a single track by file path.

        This is used to backfill durations lazily (e.g., when a track is played).
        """
        self.db.update_music_track_duration(file_path, duration)
