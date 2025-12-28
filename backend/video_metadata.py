"""Video metadata extraction from files and NFO files.

Handles extracting metadata from video files and accompanying .nfo files.
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Optional

try:
    from mutagen.mp4 import MP4, MP4StreamInfoError
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    MP4 = None
    MP4StreamInfoError = None


# NFO field mappings based on issue description
NFO_FIELD_MAP = {
    'start_time_in_ms': 'start_time_in_ms',
    'userscore': 'user_rating',
    'lastplayed': 'lastplayed',
    'title': 'title',
    'end_time_in_ms': 'end_time_in_ms',
    'Genre': 'tags',  # Map Genre to tags
    'genre': 'tags',  # Also support lowercase
    'artist': 'artist',
    'premiered': 'premiere_date',
    'plot': 'description',
    # NFO <thumb> is typically a URL or path reference, not raw image bytes.
    # Store it separately so we don't mix types with the cached thumbnail blob.
    'thumb': 'thumbnail_url',
}


def parse_nfo_file(nfo_path: str) -> dict[str, Any]:
    """Parse an NFO file and extract metadata.
    
    Args:
        nfo_path: Path to the .nfo file
        
    Returns:
        Dictionary containing extracted metadata
    """
    metadata = {}
    
    if not os.path.exists(nfo_path):
        return metadata
    
    try:
        tree = ET.parse(nfo_path)
        root = tree.getroot()
        
        # Iterate through all child elements
        for element in root:
            tag_name = element.tag  # Keep original case
            text_value = element.text
            
            if text_value is None or not text_value.strip():
                continue
            
            text_value = text_value.strip()
            
            # Map NFO fields to our metadata fields (check both original case and lowercase)
            field_name = NFO_FIELD_MAP.get(tag_name) or NFO_FIELD_MAP.get(tag_name.lower())
            
            if field_name:
                # Special handling for different field types
                if field_name == 'user_rating':
                    try:
                        metadata[field_name] = float(text_value)
                    except ValueError:
                        pass
                elif field_name == 'tags':
                    # Tags can be a list, append if already exists
                    if field_name not in metadata:
                        metadata[field_name] = []
                    if isinstance(metadata[field_name], list):
                        metadata[field_name].append(text_value)
                    else:
                        metadata[field_name] = [text_value]
                else:
                    metadata[field_name] = text_value
        
    except ET.ParseError as e:
        # Failed to parse XML, return empty metadata
        pass
    except Exception as e:
        # Any other error, return empty metadata
        pass
    
    return metadata


def read_video_metadata(
    file_path: str,
    *,
    include_duration: bool = True,
    check_nfo: bool = True,
    include_thumbnail: bool = True,
) -> dict[str, Any]:
    """Read metadata from a video file and its accompanying .nfo file.
    
    Args:
        file_path: Path to the video file
        include_duration: If True, attempt to extract duration from video
        check_nfo: If True, check for accompanying .nfo file
        include_thumbnail: If True, attempt to extract thumbnail data
        
    Returns:
        Dictionary containing extracted metadata
    """
    metadata = {}
    
    # First, try to read from video file itself (MP4 only for now)
    if MUTAGEN_AVAILABLE and include_duration:
        ext = Path(file_path).suffix.lower()
        if ext == '.mp4' or ext == '.m4v':
            try:
                video = MP4(file_path)
                if video.info and hasattr(video.info, 'length'):
                    duration = video.info.length
                    if duration and duration > 0:
                        metadata['duration'] = duration
            except Exception:
                # Failed to read MP4 metadata
                pass
    
    # Extract thumbnail data
    if include_thumbnail:
        thumbnail_data = read_thumbnail_data(file_path)
        if thumbnail_data:
            metadata['thumbnail'] = thumbnail_data[0]  # Binary data
            metadata['thumbnail_mime_type'] = thumbnail_data[1]
    
    # Check for accompanying .nfo file
    if check_nfo:
        base_path = os.path.splitext(file_path)[0]
        nfo_path = base_path + '.nfo'
        
        if os.path.exists(nfo_path):
            nfo_metadata = parse_nfo_file(nfo_path)
            # NFO metadata takes precedence for text fields.
            # Actual thumbnail image bytes are handled separately via poster file / embedded artwork.
            for key, value in nfo_metadata.items():
                metadata[key] = value
    
    return metadata


def find_nfo_file(video_path: str) -> Optional[str]:
    """Find the NFO file associated with a video file.
    
    Args:
        video_path: Path to the video file
        
    Returns:
        Path to the .nfo file if it exists, None otherwise
    """
    base_path = os.path.splitext(video_path)[0]
    nfo_path = base_path + '.nfo'
    
    if os.path.exists(nfo_path):
        return nfo_path
    
    return None


def find_poster_file(video_path: str) -> Optional[str]:
    """Find the poster image file associated with a video file.
    
    Looks for FILENAME-poster.jpg next to the video file.
    
    Args:
        video_path: Path to the video file
        
    Returns:
        Path to the poster file if it exists, None otherwise
    """
    base_path = os.path.splitext(video_path)[0]
    poster_path = base_path + '-poster.jpg'
    
    if os.path.exists(poster_path):
        return poster_path
    
    return None


def extract_embedded_thumbnail(file_path: str) -> Optional[tuple[bytes, str]]:
    """Extract embedded thumbnail from a video file.
    
    Args:
        file_path: Path to the video file
        
    Returns:
        Tuple of (thumbnail_data, mime_type) or None if not found
    """
    if not MUTAGEN_AVAILABLE:
        return None
    
    ext = Path(file_path).suffix.lower()
    if ext not in ['.mp4', '.m4v']:
        return None
    
    try:
        video = MP4(file_path)
        
        # MP4 files can have cover art in covr tag
        if 'covr' in video.tags:
            cover_art = video.tags['covr'][0]
            
            # Determine MIME type based on image format
            # MP4 cover art can be JPEG or PNG
            if hasattr(cover_art, 'imageformat'):
                if cover_art.imageformat == 13:  # JPEG
                    mime_type = 'image/jpeg'
                elif cover_art.imageformat == 14:  # PNG
                    mime_type = 'image/png'
                else:
                    mime_type = 'image/jpeg'  # Default to JPEG
            else:
                # Try to detect from magic bytes
                if bytes(cover_art)[:4] == b'\x89PNG':
                    mime_type = 'image/png'
                elif bytes(cover_art)[:2] == b'\xff\xd8':
                    mime_type = 'image/jpeg'
                else:
                    mime_type = 'image/jpeg'  # Default
            
            return bytes(cover_art), mime_type
    except Exception:
        pass
    
    return None


def read_thumbnail_data(file_path: str) -> Optional[tuple[bytes, str]]:
    """Read thumbnail data from various sources.
    
    Checks in order:
    1. FILENAME-poster.jpg file
    2. Embedded thumbnail in video file
    
    Args:
        file_path: Path to the video file
        
    Returns:
        Tuple of (thumbnail_data, mime_type) or None if not found
    """
    # First, check for poster file
    poster_path = find_poster_file(file_path)
    if poster_path:
        try:
            with open(poster_path, 'rb') as f:
                data = f.read()
                return data, 'image/jpeg'
        except Exception:
            pass
    
    # Second, try to extract from video file
    embedded = extract_embedded_thumbnail(file_path)
    if embedded:
        return embedded
    
    return None

