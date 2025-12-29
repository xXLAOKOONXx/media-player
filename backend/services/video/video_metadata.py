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

# Standard MP4/iTunes atom for the artist field (©ART).
ARTISTS_TAG = '\xa9ART'

# Standard MP4/iTunes atom for the title/name field (©nam).
TITLE_TAG = '\xa9nam'

# Some taggers store a comma-separated set of tags under a literal "tags" atom/key.
# IMPORTANT: We intentionally do NOT use MP4 genre (©gen) because it is limited.
MP4_TAGS_FIELD = 'tags'


def _coerce_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (bytes, bytearray, memoryview)):
        try:
            value = bytes(value).decode('utf-8', errors='ignore')
        except Exception:
            return None
    try:
        text = str(value).strip()
    except Exception:
        return None
    return text or None


def _normalize_tag_values(raw: Any) -> list[str]:
    """Normalize MP4 tag field values into a list[str].

    Accepts either a single string/bytes or a list of strings.
    Splits comma-separated values.
    """
    if raw is None:
        return []

    if not isinstance(raw, (list, tuple)):
        raw = [raw]

    seen: set[str] = set()
    tags: list[str] = []
    for item in raw:
        text = _coerce_text(item)
        if not text:
            continue

        # Allow either a pre-split list or a single comma-separated string.
        parts = [p.strip() for p in text.split(',')]
        for part in parts:
            if not part or part in seen:
                continue
            seen.add(part)
            tags.append(part)

    return tags


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
    # Episode number / index fields (commonly used by Kodi/Jellyfin)
    'episode': 'index_number',
    'episode_number': 'index_number',
    'track': 'index_number',
    'index': 'index_number',
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

        def _local_tag(tag: str) -> str:
            # Strip XML namespaces, if present: {ns}tag -> tag
            return tag.split('}')[-1] if tag else ''

        actor_names: list[str] = []
        artist_values: list[str] = []

        # Iterate through all child elements
        for element in root:
            tag_name = _local_tag(element.tag)  # Keep original case, minus namespaces
            tag_name_lower = tag_name.lower()

            # Special case: Kodi/Jellyfin-style actors are nested: <actor><name>...</name></actor>
            if tag_name_lower == 'actor':
                name_value: Optional[str] = None
                for child in element:
                    if _local_tag(child.tag).lower() == 'name':
                        if child.text and child.text.strip():
                            name_value = child.text.strip()
                        break
                if name_value:
                    actor_names.append(name_value)
                continue

            text_value = element.text

            if text_value is None or not text_value.strip():
                continue

            text_value = text_value.strip()

            # Map NFO fields to our metadata fields (check both original case and lowercase)
            field_name = NFO_FIELD_MAP.get(tag_name) or NFO_FIELD_MAP.get(tag_name_lower)

            if field_name:
                # Special handling for different field types
                if field_name == 'user_rating':
                    try:
                        metadata[field_name] = float(text_value)
                    except ValueError:
                        pass
                elif field_name == 'index_number':
                    try:
                        metadata[field_name] = int(float(text_value))
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
                elif field_name == 'artist':
                    artist_values.append(text_value)
                else:
                    metadata[field_name] = text_value

        if artist_values:
            # Keep order, remove duplicates
            seen: set[str] = set()
            unique_artist_values: list[str] = []
            for name in artist_values:
                if name in seen:
                    continue
                seen.add(name)
                unique_artist_values.append(name)
            metadata['artist'] = ', '.join(unique_artist_values)

        # If no explicit <artist> is provided, use actor names as artist.
        if actor_names and not metadata.get('artist'):
            # Keep order, remove duplicates
            seen: set[str] = set()
            unique_actor_names: list[str] = []
            for name in actor_names:
                if name in seen:
                    continue
                seen.add(name)
                unique_actor_names.append(name)
            metadata['artist'] = ', '.join(unique_actor_names)

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

                # Embedded title (iTunes/MP4 ©nam)
                try:
                    tags = getattr(video, 'tags', None)
                    title_raw = None
                    if tags and hasattr(tags, 'get'):
                        title_raw = tags.get(TITLE_TAG)
                    elif hasattr(video, 'get'):
                        title_raw = video.get(TITLE_TAG, [])

                    if title_raw:
                        if isinstance(title_raw, (list, tuple)):
                            title_raw = title_raw[0] if title_raw else None
                        if isinstance(title_raw, (bytes, bytearray, memoryview)):
                            try:
                                title_value = bytes(title_raw).decode('utf-8', errors='ignore')
                            except Exception:
                                title_value = None
                        else:
                            title_value = str(title_raw) if title_raw is not None else None

                        if title_value:
                            title_value = title_value.strip()
                        if title_value:
                            metadata['title'] = title_value
                except Exception:
                    pass

                # Embedded artists (iTunes/MP4 ©ART)
                try:
                    tags = getattr(video, 'tags', None)
                    artists_raw = None
                    if tags and hasattr(tags, 'get'):
                        artists_raw = tags.get(ARTISTS_TAG)
                    elif hasattr(video, 'get'):
                        artists_raw = video.get(ARTISTS_TAG, [])

                    if artists_raw:
                        if not isinstance(artists_raw, (list, tuple)):
                            artists_raw = [artists_raw]

                        seen_artists: set[str] = set()
                        artists: list[str] = []
                        for raw in artists_raw:
                            if isinstance(raw, (bytes, bytearray, memoryview)):
                                try:
                                    value = bytes(raw).decode('utf-8', errors='ignore')
                                except Exception:
                                    continue
                            else:
                                value = str(raw)

                            value = value.strip()
                            if not value or value in seen_artists:
                                continue
                            seen_artists.add(value)
                            artists.append(value)

                        if artists:
                            metadata['artist'] = ', '.join(artists)
                except Exception:
                    pass

                # Embedded tags (MP4 "tags" field)
                # IMPORTANT: Do not use MP4 genre, only the "tags" field.
                try:
                    if 'tags' not in metadata:
                        raw_tags = None
                        if hasattr(video, 'get'):
                            raw_tags = video.get(MP4_TAGS_FIELD, [])
                        else:
                            tags_obj = getattr(video, 'tags', None)
                            if tags_obj and hasattr(tags_obj, 'get'):
                                raw_tags = tags_obj.get(MP4_TAGS_FIELD, [])

                        normalized = _normalize_tag_values(raw_tags)
                        if normalized:
                            metadata['tags'] = normalized
                except Exception:
                    pass

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

