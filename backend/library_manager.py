"""
Library Manager
Handles playlist and media library management
"""

import os
from pathlib import Path


class LibraryManager:
    """Manages media libraries and playlists"""
    
    def __init__(self):
        self.libraries = {}
    
    def get_playlists(self, path):
        """Get all M3U playlists in a directory"""
        playlists = []
        
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                return playlists
            
            # Find all .m3u files
            for file in path_obj.rglob('*.m3u'):
                playlists.append({
                    'name': file.stem,
                    'path': str(file),
                    'size': file.stat().st_size
                })
            
            # Also find .m3u8 files
            for file in path_obj.rglob('*.m3u8'):
                playlists.append({
                    'name': file.stem,
                    'path': str(file),
                    'size': file.stat().st_size
                })
            
            playlists.sort(key=lambda x: x['name'].lower())
            
        except Exception as e:
            print(f"Error getting playlists: {e}")
        
        return playlists
    
    def parse_m3u(self, playlist_path):
        """Parse an M3U playlist file"""
        tracks = []
        
        try:
            with open(playlist_path, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
            
            current_track = {}
            for line in lines:
                # Strip whitespace and BOM if present
                line = line.strip()
                
                # Skip empty lines or any lines starting with # (comments/directives)
                # This includes #EXTM3U, #EXTINF:, #EXTVLCOPT:, and any other comments
                if not line or line.startswith('#'):
                    # Parse #EXTINF: directives for track metadata
                    if line.startswith('#EXTINF:'):
                        # Format: #EXTINF:duration,Artist - Title
                        parts = line[8:].split(',', 1)
                        if len(parts) == 2:
                            current_track['duration'] = parts[0]
                            current_track['title'] = parts[1]
                    continue
                
                # This is a file path (non-comment line)
                # Normalize Windows-style path separators for cross-platform compatibility.
                # Windows itself accepts '/', so this is safe on all platforms.
                if '://' not in line:
                    line = line.replace('\\', '/')
                current_track['path'] = line
                tracks.append(current_track)
                current_track = {}
            
        except Exception as e:
            print(f"Error parsing playlist: {e}")
        
        return tracks
    
    def get_tracks(self, playlist_path):
        """Get all tracks from a playlist"""
        return self.parse_m3u(playlist_path)
