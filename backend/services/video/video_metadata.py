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


# Custom MP4 freeform atoms used by this app for per-file trim points.
# These are iTunes-style freeform tags stored under the '----' atom.
START_TIME_IN_MS_TAG = '----:LAO:music-start'
END_TIME_IN_MS_TAG = '----:LAO:music-end'


def _coerce_int_ms(value: Any) -> Optional[int]:
    """Coerce an arbitrary metadata value into an integer milliseconds value."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, (bytes, bytearray, memoryview)):
        try:
            value = bytes(value).decode('utf-8', errors='ignore')
        except Exception:
            return None
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        try:
            return int(float(s))
        except ValueError:
            return None
    return None


def _read_mp4_freeform_ms_tag(video: Any, tag_name: str) -> Optional[int]:
    """Read a mutagen MP4 freeform tag and parse it as milliseconds.

    Mutagen typically returns a list of MP4FreeForm objects (bytes-like).
    """
    try:
        tags = getattr(video, 'tags', None)
        if not tags or tag_name not in tags:
            return None

        raw = tags.get(tag_name)
        if isinstance(raw, (list, tuple)) and raw:
            raw = raw[0]
        return _coerce_int_ms(raw)
    except Exception:
        return None


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
                elif field_name in ('start_time_in_ms', 'end_time_in_ms'):
                    coerced = _coerce_int_ms(text_value)
                    if coerced is not None:
                        metadata[field_name] = coerced
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
    
    # First, try to read from video file itself (MP4/M4V only for now)
    if MUTAGEN_AVAILABLE:
        ext = Path(file_path).suffix.lower()
        if ext in ('.mp4', '.m4v'):
            try:
                video = MP4(file_path)

                # Custom trim points (milliseconds)
                start_ms = _read_mp4_freeform_ms_tag(video, START_TIME_IN_MS_TAG)
                end_ms = _read_mp4_freeform_ms_tag(video, END_TIME_IN_MS_TAG)
                if start_ms is not None:
                    metadata['start_time_in_ms'] = start_ms
                if end_ms is not None:
                    metadata['end_time_in_ms'] = end_ms

                if include_duration and video.info and hasattr(video.info, 'length'):
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

