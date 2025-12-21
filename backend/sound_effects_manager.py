"""
Sound Effects Manager
Handles sound effects library management
"""

import os
from pathlib import Path


class SoundEffectsManager:
    """Manages sound effects libraries"""
    
    # Supported audio file extensions for sound effects
    AUDIO_EXTENSIONS = {'.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac'}
    
    def __init__(self):
        self.sound_effects_folders = {}
    
    def get_audio_files(self, path):
        """Get all audio files in a directory"""
        audio_files = []
        
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                return audio_files
            
            # Find all audio files (non-recursive for now)
            for file in path_obj.iterdir():
                if file.is_file() and file.suffix.lower() in self.AUDIO_EXTENSIONS:
                    audio_files.append({
                        'name': file.stem,
                        'path': str(file),
                        'size': file.stat().st_size,
                        'extension': file.suffix
                    })
            
            # Sort by name
            audio_files.sort(key=lambda x: x['name'].lower())
            
        except Exception as e:
            print(f"Error getting audio files: {e}")
        
        return audio_files
