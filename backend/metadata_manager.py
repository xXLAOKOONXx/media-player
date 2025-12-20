"""
Metadata Manager
Handles reading and writing ID3 metadata and custom tags
"""

from mutagen import File as MutagenFile
from mutagen.id3 import ID3, TXXX, TIT2, TPE1, TALB, TDRC, TRCK
import os


class MetadataManager:
    """Manages track metadata including standard ID3 tags and custom tags"""
    
    @staticmethod
    def read_metadata(file_path):
        """Read all metadata from a music file
        
        Returns dict with standard fields and custom tags
        """
        if not os.path.exists(file_path):
            return None
        
        try:
            audio = MutagenFile(file_path)
            if audio is None:
                return None
            
            metadata = {
                'title': None,
                'artist': None,
                'album': None,
                'year': None,
                'track_number': None,
                'duration': None,
                'custom_tags': {}
            }
            
            # Get duration if available
            if hasattr(audio, 'info') and hasattr(audio.info, 'length'):
                metadata['duration'] = audio.info.length
            
            # Read standard ID3 tags
            if hasattr(audio, 'tags') and audio.tags:
                tags = audio.tags
                
                # Title
                if 'TIT2' in tags:
                    metadata['title'] = str(tags['TIT2'])
                elif 'title' in tags:
                    metadata['title'] = str(tags['title'][0]) if tags['title'] else None
                
                # Artist
                if 'TPE1' in tags:
                    metadata['artist'] = str(tags['TPE1'])
                elif 'artist' in tags:
                    metadata['artist'] = str(tags['artist'][0]) if tags['artist'] else None
                
                # Album
                if 'TALB' in tags:
                    metadata['album'] = str(tags['TALB'])
                elif 'album' in tags:
                    metadata['album'] = str(tags['album'][0]) if tags['album'] else None
                
                # Year
                if 'TDRC' in tags:
                    metadata['year'] = str(tags['TDRC'])
                elif 'date' in tags:
                    metadata['year'] = str(tags['date'][0]) if tags['date'] else None
                
                # Track number
                if 'TRCK' in tags:
                    metadata['track_number'] = str(tags['TRCK'])
                elif 'tracknumber' in tags:
                    metadata['track_number'] = str(tags['tracknumber'][0]) if tags['tracknumber'] else None
                
                # Read custom TXXX tags (user-defined text information)
                txxx_frames = tags.getall('TXXX')
                for frame in txxx_frames:
                    desc = str(frame.desc) if hasattr(frame, 'desc') else ''
                    # Store all custom tags, including LAO:* pattern
                    if desc:
                        try:
                            value = str(frame.text[0]) if frame.text else ''
                            metadata['custom_tags'][desc] = value
                        except (IndexError, TypeError):
                            pass
            
            return metadata
            
        except Exception as e:
            print(f"Error reading metadata from {file_path}: {e}")
            return None
    
    @staticmethod
    def write_metadata(file_path, metadata):
        """Write metadata to a music file
        
        Args:
            file_path: Path to the music file
            metadata: Dict with fields to update:
                - title: Song title
                - artist: Artist name
                - album: Album name
                - year: Release year
                - track_number: Track number
                - custom_tags: Dict of custom tag key-value pairs
        
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(file_path):
            return False
        
        try:
            audio = MutagenFile(file_path)
            if audio is None:
                return False
            
            # Initialize ID3 tags if they don't exist
            if not hasattr(audio, 'tags') or audio.tags is None:
                audio.add_tags()
            
            tags = audio.tags
            
            # Update standard tags
            if 'title' in metadata and metadata['title'] is not None:
                tags['TIT2'] = TIT2(encoding=3, text=metadata['title'])
            
            if 'artist' in metadata and metadata['artist'] is not None:
                tags['TPE1'] = TPE1(encoding=3, text=metadata['artist'])
            
            if 'album' in metadata and metadata['album'] is not None:
                tags['TALB'] = TALB(encoding=3, text=metadata['album'])
            
            if 'year' in metadata and metadata['year'] is not None:
                tags['TDRC'] = TDRC(encoding=3, text=str(metadata['year']))
            
            if 'track_number' in metadata and metadata['track_number'] is not None:
                tags['TRCK'] = TRCK(encoding=3, text=str(metadata['track_number']))
            
            # Update custom tags
            if 'custom_tags' in metadata:
                for key, value in metadata['custom_tags'].items():
                    if key and value is not None:
                        # Remove existing TXXX frame with this description
                        existing = tags.getall('TXXX')
                        for frame in existing:
                            if hasattr(frame, 'desc') and str(frame.desc) == key:
                                tags.delall('TXXX:' + key)
                                break
                        
                        # Add new TXXX frame
                        tags.add(TXXX(encoding=3, desc=key, text=str(value)))
            
            # Save changes
            audio.save()
            return True
            
        except Exception as e:
            print(f"Error writing metadata to {file_path}: {e}")
            return False
    
    @staticmethod
    def delete_custom_tag(file_path, tag_key):
        """Delete a custom tag from a music file
        
        Args:
            file_path: Path to the music file
            tag_key: Key of the custom tag to delete
        
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(file_path):
            return False
        
        try:
            audio = MutagenFile(file_path)
            if audio is None or not hasattr(audio, 'tags') or audio.tags is None:
                return False
            
            tags = audio.tags
            
            # Remove TXXX frame with this description
            existing = tags.getall('TXXX')
            found = False
            for frame in existing:
                if hasattr(frame, 'desc') and str(frame.desc) == tag_key:
                    tags.delall('TXXX:' + tag_key)
                    found = True
                    break
            
            if found:
                audio.save()
                return True
            
            return False
            
        except Exception as e:
            print(f"Error deleting custom tag from {file_path}: {e}")
            return False
