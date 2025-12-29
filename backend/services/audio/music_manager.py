"""Music Manager

Handles music library management with ID3 metadata extraction.

Performance note:
Music folders can be on network shares (UNC). Avoid per-file full MP3 parsing
when scanning libraries, because computing accurate duration requires syncing
to MPEG frames and is extremely slow over SMB for large collections.
"""

import os
import hashlib
from pathlib import Path

from services.audio.audio_metadata import (
    MUTAGEN_AVAILABLE,
    compute_duration_seconds,
    display_title,
    read_audio_metadata,
)

from services.audio.music_cache import MusicCache


class MusicManager:
    """Manages music libraries and tracks with metadata"""
    
    # Supported audio file extensions
    AUDIO_EXTENSIONS = {'.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac', '.opus'}
    
    def __init__(self, use_cache=True):
        self.cache = MusicCache() if use_cache else None
    
    def get_audio_files(
        self,
        path,
        recursive=False,
        folder_id=None,
        force_refresh=False,
        include_duration=False,
    ):
        """Get all audio files in a directory
        
        Args:
            path: Directory path to scan
            recursive: If True, scan subdirectories as well
            folder_id: Optional folder ID for caching
            force_refresh: If True, bypass cache and rescan
            
        Returns:
            List of dicts with file information and metadata
        """
        # Try to use cache if available
        if self.cache and folder_id is not None and not force_refresh:
            # Register folder in cache
            self.cache.register_folder(folder_id, path, recursive)
            
            # Try to get from cache
            cached_tracks = self.cache.get_cached_tracks(folder_id)
            if cached_tracks is not None:
                return cached_tracks
        
        # Cache miss or force refresh - scan filesystem
        # If we're going to cache results, it's worth computing duration once during the scan.
        # This avoids re-opening files later and keeps subsequent calls fast.
        scan_include_duration = include_duration or (self.cache is not None and folder_id is not None)
        audio_files = self._scan_audio_files(path, recursive, include_duration=scan_include_duration)
        
        # Update cache
        if self.cache and folder_id is not None:
            self.cache.cache_tracks(folder_id, audio_files)
        
        return audio_files
    
    def _scan_audio_files(self, path, recursive=False, include_duration=False):
        """Scan filesystem for audio files
        
        Args:
            path: Directory path to scan
            recursive: If True, scan subdirectories as well
            
        Returns:
            List of dicts with file information and metadata
        """
        audio_files = []
        
        try:
            # Prefer os.scandir/os.walk over pathlib rglob on Windows/UNC shares.
            if not os.path.exists(path):
                return audio_files

            def handle_file(full_path: str, file_name: str):
                ext = os.path.splitext(file_name)[1].lower()
                if ext not in self.AUDIO_EXTENSIONS:
                    return

                try:
                    stat = os.stat(full_path)
                except OSError:
                    return

                normalized_path = os.path.normpath(full_path)
                media_id = hashlib.sha256(normalized_path.encode('utf-8', errors='replace')).hexdigest()

                file_info = {
                    'name': file_name,
                    'path': normalized_path,
                    'media_id': media_id,
                    'size': stat.st_size,
                    'last_modified': stat.st_mtime,
                }

                if MUTAGEN_AVAILABLE:
                    metadata = read_audio_metadata(
                        normalized_path,
                        include_duration=include_duration,
                        include_times=False,
                        include_tags=True,
                    )
                    file_info.update(metadata)

                # Ensure consistent title fallback across Music + Player.
                file_info['title'] = display_title(file_info)

                audio_files.append(file_info)

            if recursive:
                for root, _dirs, files in os.walk(path):
                    for name in files:
                        handle_file(os.path.join(root, name), name)
            else:
                with os.scandir(path) as it:
                    for entry in it:
                        if entry.is_file():
                            handle_file(entry.path, entry.name)
            
            # Sort by artist, then title
            audio_files.sort(key=lambda x: (
                x.get('artist', '').lower(),
                x.get('title', x.get('name', '')).lower()
            ))
            
        except Exception as e:
            print(f"Error getting audio files: {e}")
        
        return audio_files
    
    def invalidate_cache(self, folder_id):
        """Invalidate cache for a folder"""
        if self.cache:
            self.cache.invalidate_folder(folder_id)

    def compute_duration_seconds(self, file_path):
        """Compute duration in seconds for a single audio file (best-effort).

        Cross-platform: relies on mutagen only.
        Returns float seconds or None if duration can't be determined.
        """
        return compute_duration_seconds(file_path)

    def backfill_cached_duration(self, file_path, duration_seconds):
        """Persist a duration into the cache if caching is enabled."""
        if not self.cache:
            return
        try:
            self.cache.update_track_duration(file_path, duration_seconds)
        except Exception:
            # Cache failures shouldn't break playback.
            pass
    
    
    def search_tracks(self, tracks, artist=None, duration_min=None, duration_max=None, 
                     tags=None, title=None):
        """Filter tracks by search criteria
        
        Args:
            tracks: List of track dicts
            artist: Filter by artist name (case-insensitive partial match)
            duration_min: Minimum duration in seconds
            duration_max: Maximum duration in seconds
            tags: List of tags to filter by (track must have at least one)
            title: Filter by title (case-insensitive partial match)
            
        Returns:
            Filtered list of tracks
        """
        filtered = tracks
        
        if artist:
            artist_lower = artist.lower()
            filtered = [t for t in filtered 
                       if artist_lower in t.get('artist', '').lower()]
        
        if duration_min is not None:
            filtered = [t for t in filtered 
                       if t.get('duration', 0) >= duration_min]
        
        if duration_max is not None:
            filtered = [t for t in filtered 
                       if t.get('duration', float('inf')) <= duration_max]
        
        if tags:
            # Track must have at least one of the specified tags
            filtered = [t for t in filtered 
                       if any(tag in t.get('tags', []) for tag in tags)]
        
        if title:
            title_lower = title.lower()
            filtered = [t for t in filtered 
                       if title_lower in t.get('title', '').lower()]
        
        return filtered
    
    def create_playlist(self, playlist_path, tracks, base_path=None):
        """Create an M3U playlist file
        
        Args:
            playlist_path: Path where to save the M3U file
            tracks: List of track dicts with 'path' key
            base_path: Base path for calculating relative paths (if None, uses absolute)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            playlist_path_obj = Path(playlist_path)
            
            # Create directory if it doesn't exist
            playlist_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            with open(playlist_path, 'w', encoding='utf-8') as f:
                f.write('#EXTM3U\n')
                
                for track in tracks:
                    track_path = track.get('path')
                    if not track_path:
                        continue
                    
                    # Write EXTINF line with duration and title
                    duration = int(track.get('duration', 0))
                    title = track.get('title', Path(track_path).name)
                    artist = track.get('artist', '')
                    
                    if artist:
                        display_name = f"{artist} - {title}"
                    else:
                        display_name = title
                    
                    f.write(f'#EXTINF:{duration},{display_name}\n')
                    
                    # Write track path (relative if base_path provided)
                    if base_path:
                        try:
                            track_path_obj = Path(track_path)
                            base_path_obj = Path(base_path)
                            relative_path = os.path.relpath(track_path_obj, base_path_obj)
                            f.write(f'{relative_path}\n')
                        except ValueError:
                            # Can't make relative path (different drives on Windows)
                            f.write(f'{track_path}\n')
                    else:
                        f.write(f'{track_path}\n')
            
            return True
            
        except Exception as e:
            print(f"Error creating playlist: {e}")
            return False
    
    def add_track_to_playlist(self, playlist_path, track, base_path=None):
        """Add a track to an existing M3U playlist
        
        Args:
            playlist_path: Path to the M3U file
            track: Track dict with 'path' key
            base_path: Base path for calculating relative paths
            
        Returns:
            True if successful, False if track already exists or error
        """
        try:
            # Validate track file exists before adding
            track_path = track.get('path')
            if not track_path:
                return False
            
            if not os.path.exists(track_path):
                print(f"Warning: Track file does not exist: {track_path}")
                return False
            
            # Read existing playlist
            existing_tracks = []
            if os.path.exists(playlist_path):
                with open(playlist_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            existing_tracks.append(line)
            
            if base_path:
                try:
                    track_path_obj = Path(track_path)
                    base_path_obj = Path(base_path)
                    relative_path = os.path.relpath(track_path_obj, base_path_obj)
                except ValueError:
                    relative_path = track_path
            else:
                relative_path = track_path
            
            # Check if track already exists (normalize paths for comparison)
            normalized_relative = os.path.normpath(relative_path)
            for existing in existing_tracks:
                if os.path.normpath(existing) == normalized_relative:
                    return False  # Track already exists
            
            # Append track to playlist
            with open(playlist_path, 'a', encoding='utf-8') as f:
                # Write EXTINF line
                duration = int(track.get('duration', 0))
                title = track.get('title', Path(track_path).name)
                artist = track.get('artist', '')
                
                if artist:
                    display_name = f"{artist} - {title}"
                else:
                    display_name = title
                
                f.write(f'#EXTINF:{duration},{display_name}\n')
                f.write(f'{relative_path}\n')
            
            return True
            
        except Exception as e:
            print(f"Error adding track to playlist: {e}")
            return False
