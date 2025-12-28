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
    'thumb': 'thumbnail',
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
) -> dict[str, Any]:
    """Read metadata from a video file and its accompanying .nfo file.
    
    Args:
        file_path: Path to the video file
        include_duration: If True, attempt to extract duration from video
        check_nfo: If True, check for accompanying .nfo file
        
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
    
    # Check for accompanying .nfo file
    if check_nfo:
        base_path = os.path.splitext(file_path)[0]
        nfo_path = base_path + '.nfo'
        
        if os.path.exists(nfo_path):
            nfo_metadata = parse_nfo_file(nfo_path)
            # NFO metadata takes precedence for all fields
            metadata.update(nfo_metadata)
    
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
