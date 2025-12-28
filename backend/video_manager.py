"""Video Manager

Handles video library management with basic metadata extraction.
"""

import os
from pathlib import Path


class VideoManager:
    """Manages video libraries and tracks"""
    
    # Supported video file extensions
    VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg'}
    
    def __init__(self):
        pass
    
    def get_video_files(self, path, recursive=False):
        """Get all video files in a directory
        
        Args:
            path: Directory path to scan
            recursive: If True, scan subdirectories as well
            
        Returns:
            List of dicts with file information
        """
        video_files = []
        
        try:
            if not os.path.exists(path):
                return video_files

            def handle_file(full_path: str, file_name: str):
                ext = os.path.splitext(file_name)[1].lower()
                if ext not in self.VIDEO_EXTENSIONS:
                    return

                try:
                    stat = os.stat(full_path)
                except OSError:
                    return

                # Create track info
                video_info = {
                    'path': full_path,
                    'name': file_name,
                    'title': os.path.splitext(file_name)[0],
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                }
                
                video_files.append(video_info)

            if recursive:
                for root, dirs, files in os.walk(path):
                    for file_name in files:
                        full_path = os.path.join(root, file_name)
                        handle_file(full_path, file_name)
            else:
                with os.scandir(path) as entries:
                    for entry in entries:
                        if entry.is_file():
                            handle_file(entry.path, entry.name)
                            
        except Exception as e:
            print(f"Error scanning video directory {path}: {e}")
        
        # Sort by name
        video_files.sort(key=lambda x: x['name'].lower())
        return video_files
    
    def create_playlist(self, playlist_path, videos, base_path=None):
        """Create an M3U playlist file from a list of videos
        
        Args:
            playlist_path: Full path where the playlist file will be created
            videos: List of video dicts with 'path' key
            base_path: Optional base path to make video paths relative to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            playlist_dir = os.path.dirname(playlist_path)
            
            with open(playlist_path, 'w', encoding='utf-8') as f:
                f.write('#EXTM3U\n')
                
                for video in videos:
                    video_path = video.get('path', '')
                    if not video_path:
                        continue
                    
                    # Make path relative to playlist directory if possible
                    if base_path and os.path.isabs(video_path):
                        try:
                            video_path = os.path.relpath(video_path, playlist_dir)
                        except ValueError:
                            # Can't make relative (different drives on Windows)
                            pass
                    
                    # Write extended info
                    title = video.get('title', os.path.basename(video_path))
                    f.write(f'#EXTINF:-1,{title}\n')
                    f.write(f'{video_path}\n')
            
            return True
        except Exception as e:
            print(f"Error creating playlist {playlist_path}: {e}")
            return False
    
    def search_videos(self, videos, title=None):
        """Filter videos by search criteria
        
        Args:
            videos: List of video dicts
            title: Filter by title (case-insensitive substring match)
            
        Returns:
            Filtered list of videos
        """
        filtered = videos
        
        if title:
            title_lower = title.lower()
            filtered = [
                v for v in filtered 
                if title_lower in v.get('title', '').lower() or 
                   title_lower in v.get('name', '').lower()
            ]
        
        return filtered
