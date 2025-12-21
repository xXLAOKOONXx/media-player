"""
Music Manager
Handles music library management with ID3 metadata extraction
"""

import os
from pathlib import Path

try:
    from mutagen import File as MutagenFile
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    print("Warning: mutagen not available, ID3 tag reading disabled")

from music_cache import MusicCache


class MusicManager:
    """Manages music libraries and tracks with metadata"""
    
    # Supported audio file extensions
    AUDIO_EXTENSIONS = {'.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac', '.wma', '.opus'}
    
    def __init__(self, use_cache=True):
        self.cache = MusicCache() if use_cache else None
    
    def get_audio_files(self, path, recursive=False, folder_id=None, force_refresh=False):
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
        audio_files = self._scan_audio_files(path, recursive)
        
        # Update cache
        if self.cache and folder_id is not None:
            self.cache.cache_tracks(folder_id, audio_files)
        
        return audio_files
    
    def _scan_audio_files(self, path, recursive=False):
        """Scan filesystem for audio files
        
        Args:
            path: Directory path to scan
            recursive: If True, scan subdirectories as well
            
        Returns:
            List of dicts with file information and metadata
        """
        audio_files = []
        
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                return audio_files
            
            # Get audio files based on recursive setting
            if recursive:
                file_iterator = path_obj.rglob('*')
            else:
                file_iterator = path_obj.glob('*')
            
            for file in file_iterator:
                if file.is_file() and file.suffix.lower() in self.AUDIO_EXTENSIONS:
                    file_info = {
                        'name': file.name,
                        'path': str(file),
                        'size': file.stat().st_size
                    }
                    
                    # Extract metadata
                    metadata = self._extract_metadata(str(file))
                    file_info.update(metadata)
                    
                    audio_files.append(file_info)
            
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
    
    def _extract_metadata(self, file_path):
        """Extract metadata from audio file
        
        Returns dict with artist, title, album, duration, and tags
        """
        if not MUTAGEN_AVAILABLE:
            return {}
        
        try:
            audio = MutagenFile(file_path)
            if audio is None:
                return {}
            
            metadata = {}
            
            # Extract duration
            if hasattr(audio.info, 'length'):
                metadata['duration'] = audio.info.length
            
            # Extract tags
            if hasattr(audio, 'tags') and audio.tags:
                # Extract artist
                artist = self._get_tag_value(audio.tags, ['TPE1', 'artist', '\xa9ART'])
                if artist:
                    metadata['artist'] = artist
                
                # Extract title
                title = self._get_tag_value(audio.tags, ['TIT2', 'title', '\xa9nam'])
                if title:
                    metadata['title'] = title
                
                # Extract album
                album = self._get_tag_value(audio.tags, ['TALB', 'album', '\xa9alb'])
                if album:
                    metadata['album'] = album
                
                # Extract custom LAO:TAGS field
                tags = self._get_custom_tag(audio.tags, 'LAO:TAGS')
                if tags:
                    # Parse stringified list
                    try:
                        # Handle different formats: "['tag1', 'tag2']" or "tag1,tag2"
                        import json
                        if tags.startswith('[') and tags.endswith(']'):
                            metadata['tags'] = json.loads(tags.replace("'", '"'))
                        else:
                            metadata['tags'] = [t.strip() for t in tags.split(',')]
                    except:
                        metadata['tags'] = [tags]
            
            return metadata
            
        except Exception as e:
            print(f"Error extracting metadata from {file_path}: {e}")
            return {}
    
    def _get_tag_value(self, tags, tag_names):
        """Get value from various tag formats
        
        Args:
            tags: Audio tags object
            tag_names: List of possible tag names to try
            
        Returns:
            String value or None
        """
        for tag_name in tag_names:
            try:
                if hasattr(tags, 'get'):
                    tag = tags.get(tag_name)
                    if tag:
                        # Handle different tag value formats
                        if isinstance(tag, list):
                            return str(tag[0]) if tag else None
                        elif hasattr(tag, 'text'):
                            return str(tag.text[0]) if tag.text else None
                        else:
                            return str(tag)
            except (AttributeError, TypeError, IndexError, KeyError):
                continue
        return None
    
    def _get_custom_tag(self, tags, tag_name):
        """Get custom TXXX tag value
        
        Args:
            tags: Audio tags object
            tag_name: Name of the custom tag (e.g., 'LAO:TAGS')
            
        Returns:
            String value or None
        """
        try:
            # For ID3v2 TXXX frames
            if hasattr(tags, 'getall'):
                txxx_frames = tags.getall('TXXX')
                for frame in txxx_frames:
                    if hasattr(frame, 'desc') and str(frame.desc) == tag_name:
                        if hasattr(frame, 'text') and frame.text:
                            return str(frame.text[0])
            
            # For other formats, try direct access
            if hasattr(tags, 'get'):
                tag = tags.get(tag_name)
                if tag:
                    if isinstance(tag, list):
                        return str(tag[0]) if tag else None
                    return str(tag)
        except Exception:
            pass
        
        return None
    
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
