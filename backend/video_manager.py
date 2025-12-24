"""Video Manager

Handles video library management.
"""

import os


class VideoManager:
    """Manages video libraries and files"""
    
    # Supported video file extensions
    VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
    
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

                file_info = {
                    'name': file_name,
                    'path': full_path,
                    'size': stat.st_size,
                    'title': os.path.splitext(file_name)[0],  # Use filename without extension as title
                }

                video_files.append(file_info)

            if recursive:
                for root, _dirs, files in os.walk(path):
                    for name in files:
                        handle_file(os.path.join(root, name), name)
            else:
                with os.scandir(path) as it:
                    for entry in it:
                        if entry.is_file():
                            handle_file(entry.path, entry.name)
            
            # Sort by title
            video_files.sort(key=lambda x: x.get('title', x.get('name', '')).lower())
            
        except Exception as e:
            print(f"Error getting video files: {e}")
        
        return video_files
    
    def get_playlists(self, playlist_folder):
        """Get all playlists in the configured folder
        
        Args:
            playlist_folder: Path to the playlist folder
            
        Returns:
            List of playlist dicts with name and path
        """
        playlists = []
        
        try:
            if not os.path.exists(playlist_folder):
                return playlists
            
            with os.scandir(playlist_folder) as it:
                for entry in it:
                    if entry.is_file() and entry.name.lower().endswith('.m3u'):
                        playlists.append({
                            'name': os.path.splitext(entry.name)[0],
                            'path': entry.path
                        })
            
            playlists.sort(key=lambda x: x['name'].lower())
            
        except Exception as e:
            print(f"Error getting playlists: {e}")
        
        return playlists
