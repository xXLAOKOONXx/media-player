"""Shared audio metadata and display helpers.

Goal: keep title/metadata extraction consistent between the Music library view
and the Player view.

This module is intentionally cross-platform (Windows/Linux/macOS). It relies on
mutagen only and does not use OS-specific media APIs.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:
    from mutagen import File as MutagenFile  # type: ignore
    from mutagen.id3 import ID3  # type: ignore
    from mutagen.mp3 import MP3, HeaderNotFoundError  # type: ignore

    MUTAGEN_AVAILABLE = True
except Exception:  # pragma: no cover
    MUTAGEN_AVAILABLE = False
    MutagenFile = None  # type: ignore
    ID3 = None  # type: ignore
    MP3 = None  # type: ignore
    HeaderNotFoundError = None  # type: ignore


def filename_stem_from_path(value: str) -> str:
    """Best-effort filename (no extension) from a local path or URL."""
    if not value:
        return ''

    # Be conservative: M3U can contain http(s) streams.
    if '://' in value or value.startswith(('http:', 'https:')):
        normalized = value.replace('\\', '/')
        last = normalized.rsplit('/', 1)[-1]
        return os.path.splitext(last)[0]

    return os.path.splitext(os.path.basename(value))[0]


def display_title(track: dict) -> str:
    """Return the display title for a track dict.

    Priority:
    1) track['title'] if non-empty
    2) track['name'] (library scan) without extension
    3) filename stem derived from track['path']
    4) "Unknown"
    """
    title = track.get('title')
    if isinstance(title, str) and title.strip():
        return title

    name = track.get('name')
    if isinstance(name, str) and name.strip():
        return os.path.splitext(name)[0]

    path = track.get('path')
    if isinstance(path, str) and path.strip():
        stem = filename_stem_from_path(path)
        return stem if stem else 'Unknown'

    return 'Unknown'


def _get_tag_value(tags: Any, tag_names: list[str]) -> str | None:
    for tag_name in tag_names:
        try:
            if hasattr(tags, 'get'):
                tag = tags.get(tag_name)
                if not tag:
                    continue

                if isinstance(tag, list):
                    return str(tag[0]) if tag else None

                if hasattr(tag, 'text'):
                    return str(tag.text[0]) if tag.text else None

                return str(tag)
        except (AttributeError, TypeError, IndexError, KeyError):
            continue
    return None


def _get_custom_tag(tags: Any, tag_name: str) -> str | None:
    """Get custom tag value.

    Supports ID3 TXXX frames where frame.desc == tag_name.
    """
    try:
        if hasattr(tags, 'getall'):
            txxx_frames = tags.getall('TXXX')
            for frame in txxx_frames:
                if hasattr(frame, 'desc') and str(frame.desc) == tag_name:
                    if hasattr(frame, 'text') and frame.text:
                        return str(frame.text[0])

        if hasattr(tags, 'get'):
            tag = tags.get(tag_name)
            if tag:
                if isinstance(tag, list):
                    return str(tag[0]) if tag else None
                return str(tag)
    except Exception:
        pass

    return None


def _parse_lao_tags(value: str) -> list[str]:
    if not value:
        return []

    try:
        import json

        if value.startswith('[') and value.endswith(']'):
            return list(json.loads(value.replace("'", '"')))
        return [t.strip() for t in value.split(',') if t.strip()]
    except Exception:
        return [value]


def read_audio_metadata(
    file_path: str,
    *,
    include_duration: bool = False,
    include_times: bool = False,
    include_tags: bool = True,
) -> dict:
    """Read metadata from an audio file (best-effort).

    Returned keys (when available):
    - artist, title, album
    - duration (seconds)
    - tags (list[str]) from custom LAO:TAGS
    - start_time/end_time (seconds) from custom LAO:MUSIC_START/LAO:MUSIC_END (ms in file)

    Cross-platform.
    """
    if not MUTAGEN_AVAILABLE:
        return {}

    ext = Path(file_path).suffix.lower()
    metadata: dict[str, Any] = {}

    # --- MP3 ---
    if ext == '.mp3':
        tags_obj = None

        # ID3 tags (optional)
        if ID3 is not None:
            try:
                tags_obj = ID3(file_path)
            except Exception:
                tags_obj = None

        if tags_obj is not None:
            artist = _get_tag_value(tags_obj, ['TPE1', 'artist', '\xa9ART'])
            if artist:
                metadata['artist'] = artist

            title = _get_tag_value(tags_obj, ['TIT2', 'title', '\xa9nam'])
            if title:
                metadata['title'] = title

            album = _get_tag_value(tags_obj, ['TALB', 'album', '\xa9alb'])
            if album:
                metadata['album'] = album

            if include_tags:
                lao_tags = _get_custom_tag(tags_obj, 'LAO:TAGS')
                if lao_tags:
                    metadata['tags'] = _parse_lao_tags(lao_tags)

            if include_times:
                try:
                    txxx_frames = tags_obj.getall('TXXX') if hasattr(tags_obj, 'getall') else []
                    for frame in txxx_frames:
                        desc = str(frame.desc) if hasattr(frame, 'desc') else ''
                        if desc == 'LAO:MUSIC_START':
                            try:
                                metadata['start_time'] = float(frame.text[0]) / 1000.0
                            except (ValueError, IndexError, TypeError):
                                pass
                        elif desc == 'LAO:MUSIC_END':
                            try:
                                metadata['end_time'] = float(frame.text[0]) / 1000.0
                            except (ValueError, IndexError, TypeError):
                                pass
                except Exception:
                    pass

        # Duration (may require MPEG frame sync)
        if include_duration:
            try:
                if MP3 is not None:
                    mp3 = MP3(file_path)
                    if hasattr(mp3, 'info') and hasattr(mp3.info, 'length'):
                        metadata['duration'] = float(mp3.info.length)
                else:
                    audio = MutagenFile(file_path) if MutagenFile is not None else None
                    if audio is not None and hasattr(audio, 'info') and hasattr(audio.info, 'length'):
                        metadata['duration'] = float(audio.info.length)
            except Exception as e:
                # Fall back to TLEN if available
                if (HeaderNotFoundError is not None and isinstance(e, HeaderNotFoundError)) or "can't sync to MPEG frame" in str(e):
                    pass
                else:
                    raise

            if 'duration' not in metadata and tags_obj is not None:
                try:
                    tlen = tags_obj.get('TLEN') if hasattr(tags_obj, 'get') else None
                    if tlen is not None and hasattr(tlen, 'text') and tlen.text:
                        metadata['duration'] = float(tlen.text[0]) / 1000.0
                except Exception:
                    pass

        return metadata

    # --- Other formats ---
    audio = MutagenFile(file_path) if MutagenFile is not None else None
    if audio is None:
        return {}

    if include_duration and hasattr(audio, 'info') and hasattr(audio.info, 'length'):
        metadata['duration'] = float(audio.info.length)

    if hasattr(audio, 'tags') and audio.tags:
        artist = _get_tag_value(audio.tags, ['TPE1', 'artist', '\xa9ART'])
        if artist:
            metadata['artist'] = artist

        title = _get_tag_value(audio.tags, ['TIT2', 'title', '\xa9nam'])
        if title:
            metadata['title'] = title

        album = _get_tag_value(audio.tags, ['TALB', 'album', '\xa9alb'])
        if album:
            metadata['album'] = album

        if include_tags:
            lao_tags = _get_custom_tag(audio.tags, 'LAO:TAGS')
            if lao_tags:
                metadata['tags'] = _parse_lao_tags(lao_tags)

        if include_times:
            try:
                txxx_frames = audio.tags.getall('TXXX') if hasattr(audio.tags, 'getall') else []
                for frame in txxx_frames:
                    desc = str(frame.desc) if hasattr(frame, 'desc') else ''
                    if desc == 'LAO:MUSIC_START':
                        try:
                            metadata['start_time'] = float(frame.text[0]) / 1000.0
                        except (ValueError, IndexError, TypeError):
                            pass
                    elif desc == 'LAO:MUSIC_END':
                        try:
                            metadata['end_time'] = float(frame.text[0]) / 1000.0
                        except (ValueError, IndexError, TypeError):
                            pass
            except Exception:
                pass

    return metadata


def compute_duration_seconds(file_path: str) -> float | None:
    """Compute duration for a single file (best-effort)."""
    if not MUTAGEN_AVAILABLE:
        return None

    ext = Path(file_path).suffix.lower()

    try:
        if ext == '.mp3' and MP3 is not None:
            audio = MP3(file_path)
        else:
            audio = MutagenFile(file_path) if MutagenFile is not None else None

        if audio is None:
            return None

        if hasattr(audio, 'info') and hasattr(audio.info, 'length'):
            return float(audio.info.length)
    except Exception:
        return None

    return None
