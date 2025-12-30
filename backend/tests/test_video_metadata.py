"""Tests for video metadata extraction from NFO files."""

import os
import tempfile
import pytest
from pathlib import Path

from services.video.video_metadata import (
    parse_nfo_file,
    read_video_metadata,
    find_nfo_file,
    update_nfo_user_rating_and_tags,
    update_nfo_user_metadata,
)


class TestNFOParsing:
    """Test NFO file parsing functionality."""
    
    def test_parse_simple_nfo(self):
        """Test parsing a simple NFO file with basic metadata."""
        nfo_content = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<movie>
    <title>Test Movie</title>
    <plot>This is a test movie description.</plot>
    <premiered>2023-01-15</premiered>
    <Genre>Action</Genre>
    <Genre>Adventure</Genre>
</movie>
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.nfo', delete=False) as f:
            f.write(nfo_content)
            nfo_path = f.name
        
        try:
            metadata = parse_nfo_file(nfo_path)
            
            assert metadata['title'] == 'Test Movie'
            assert metadata['description'] == 'This is a test movie description.'
            assert metadata['premiere_date'] == '2023-01-15'
            assert 'tags' in metadata
            assert isinstance(metadata['tags'], list)
            assert 'Action' in metadata['tags']
            assert 'Adventure' in metadata['tags']
        finally:
            os.unlink(nfo_path)
    
    def test_parse_nfo_with_user_rating(self):
        """Test parsing NFO with user rating."""
        nfo_content = """<?xml version="1.0" encoding="UTF-8"?>
<movie>
    <title>Rated Movie</title>
    <userscore>8.5</userscore>
</movie>
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.nfo', delete=False) as f:
            f.write(nfo_content)
            nfo_path = f.name
        
        try:
            metadata = parse_nfo_file(nfo_path)
            
            assert metadata['title'] == 'Rated Movie'
            assert 'user_rating' in metadata
            assert metadata['user_rating'] == 8.5
            assert isinstance(metadata['user_rating'], float)
        finally:
            os.unlink(nfo_path)

    def test_update_nfo_user_rating_and_tags_replaces_existing(self):
        nfo_content = """<?xml version="1.0" encoding="UTF-8"?>
<movie>
    <title>Test Movie</title>
    <userscore>4.0</userscore>
    <Genre>OldOne</Genre>
    <genre>OldTwo</genre>
</movie>
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.nfo', delete=False) as f:
            f.write(nfo_content)
            nfo_path = f.name

        try:
            ok = update_nfo_user_rating_and_tags(nfo_path, user_rating=8.5, tags=['Action', 'Adventure'])
            assert ok is True

            metadata = parse_nfo_file(nfo_path)
            assert metadata.get('user_rating') == 8.5
            assert sorted(metadata.get('tags') or []) == ['Action', 'Adventure']
        finally:
            os.unlink(nfo_path)

    def test_update_nfo_user_rating_and_tags_removes_when_none(self):
        nfo_content = """<?xml version="1.0" encoding="UTF-8"?>
<movie>
    <title>Test Movie</title>
    <userscore>7.0</userscore>
    <Genre>Action</Genre>
</movie>
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.nfo', delete=False) as f:
            f.write(nfo_content)
            nfo_path = f.name

        try:
            ok = update_nfo_user_rating_and_tags(nfo_path, user_rating=None, tags=[])
            assert ok is True

            metadata = parse_nfo_file(nfo_path)
            assert 'user_rating' not in metadata
            assert metadata.get('tags') in (None, [])
        finally:
            os.unlink(nfo_path)
    
    def test_parse_nfo_with_artist(self):
        """Test parsing NFO with artist information."""
        nfo_content = """<?xml version="1.0" encoding="UTF-8"?>
<video>
    <title>Music Video</title>
    <artist>John Doe</artist>
    <plot>A great music video</plot>
</video>
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.nfo', delete=False) as f:
            f.write(nfo_content)
            nfo_path = f.name
        
        try:
            metadata = parse_nfo_file(nfo_path)
            
            assert metadata['title'] == 'Music Video'
            assert metadata['artist'] == 'John Doe'
            assert metadata['description'] == 'A great music video'
        finally:
            os.unlink(nfo_path)

    def test_parse_nfo_uses_actor_names_for_artist(self):
        """If <artist> is missing, use <actor><name>... as artist (joined)."""
        nfo_content = """<?xml version="1.0" encoding="UTF-8"?>
<movie>
    <title>Actor Movie</title>
    <actor>
        <name>Michael Herbig</name>
    </actor>
    <actor>
        <name>Rick Kavanian</name>
    </actor>
</movie>
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.nfo', delete=False) as f:
            f.write(nfo_content)
            nfo_path = f.name

        try:
            metadata = parse_nfo_file(nfo_path)
            assert metadata['title'] == 'Actor Movie'
            assert metadata['artist'] == 'Michael Herbig, Rick Kavanian'
        finally:
            os.unlink(nfo_path)

    def test_parse_nfo_multiple_artist_tags_joined_with_commas(self):
        """Multiple <artist> tags should be joined with commas."""
        nfo_content = """<?xml version="1.0" encoding="UTF-8"?>
<movie>
    <title>Multi Artist Movie</title>
    <artist>Artist One</artist>
    <artist>Artist Two</artist>
</movie>
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.nfo', delete=False) as f:
            f.write(nfo_content)
            nfo_path = f.name

        try:
            metadata = parse_nfo_file(nfo_path)
            assert metadata['title'] == 'Multi Artist Movie'
            assert metadata['artist'] == 'Artist One, Artist Two'
        finally:
            os.unlink(nfo_path)
    
    def test_parse_nfo_with_thumbnail(self):
        """Test parsing NFO with thumbnail URL."""
        nfo_content = """<?xml version="1.0" encoding="UTF-8"?>
<movie>
    <title>Movie with Thumbnail</title>
    <thumb>https://example.com/poster.jpg</thumb>
</movie>
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.nfo', delete=False) as f:
            f.write(nfo_content)
            nfo_path = f.name
        
        try:
            metadata = parse_nfo_file(nfo_path)
            
            assert metadata['title'] == 'Movie with Thumbnail'
            assert metadata['thumbnail_url'] == 'https://example.com/poster.jpg'
        finally:
            os.unlink(nfo_path)
    
    def test_parse_nonexistent_nfo(self):
        """Test parsing a non-existent NFO file."""
        metadata = parse_nfo_file('/nonexistent/path/file.nfo')
        assert metadata == {}
    
    def test_parse_invalid_xml(self):
        """Test parsing invalid XML gracefully."""
        nfo_content = """This is not valid XML
<unclosed tag
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.nfo', delete=False) as f:
            f.write(nfo_content)
            nfo_path = f.name
        
        try:
            metadata = parse_nfo_file(nfo_path)
            # Should return empty dict on parse error
            assert metadata == {}
        finally:
            os.unlink(nfo_path)
    
    def test_parse_empty_nfo(self):
        """Test parsing an empty NFO file."""
        nfo_content = """<?xml version="1.0" encoding="UTF-8"?>
<movie>
</movie>
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.nfo', delete=False) as f:
            f.write(nfo_content)
            nfo_path = f.name
        
        try:
            metadata = parse_nfo_file(nfo_path)
            # Should return empty dict
            assert metadata == {}
        finally:
            os.unlink(nfo_path)

    def test_parse_nfo_with_custom_times_ms(self):
        """NFO start/end times should be parsed as integer milliseconds when numeric."""
        nfo_content = """<?xml version="1.0" encoding="UTF-8"?>
<movie>
    <title>Timed Movie</title>
    <start_time_in_ms>1200</start_time_in_ms>
    <end_time_in_ms>3456</end_time_in_ms>
</movie>
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.nfo', delete=False) as f:
            f.write(nfo_content)
            nfo_path = f.name

        try:
            metadata = parse_nfo_file(nfo_path)
            assert metadata['start_time_in_ms'] == 1200
            assert metadata['end_time_in_ms'] == 3456
        finally:
            os.unlink(nfo_path)


class TestVideoMetadataExtraction:
    """Test video metadata extraction with NFO files."""
    
    def test_read_metadata_with_nfo(self):
        """Test reading metadata from a video file with accompanying NFO."""
        # Create a temporary video file (just touch it, doesn't need to be real)
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as video_file:
            video_path = video_file.name
        
        # Create accompanying NFO file
        nfo_path = os.path.splitext(video_path)[0] + '.nfo'
        nfo_content = """<?xml version="1.0" encoding="UTF-8"?>
<movie>
    <title>Test Video</title>
    <artist>Test Artist</artist>
    <Genre>Documentary</Genre>
    <userscore>9.0</userscore>
</movie>
"""
        with open(nfo_path, 'w') as f:
            f.write(nfo_content)
        
        try:
            metadata = read_video_metadata(video_path, include_duration=False)
            
            assert metadata['title'] == 'Test Video'
            assert metadata['artist'] == 'Test Artist'
            assert 'Documentary' in metadata['tags']
            assert metadata['user_rating'] == 9.0
        finally:
            os.unlink(video_path)
            if os.path.exists(nfo_path):
                os.unlink(nfo_path)
    
    def test_read_metadata_without_nfo(self):
        """Test reading metadata from a video file without NFO."""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as video_file:
            video_path = video_file.name
        
        try:
            metadata = read_video_metadata(video_path, include_duration=False)
            # Should return empty or minimal metadata
            assert isinstance(metadata, dict)
        finally:
            os.unlink(video_path)

    def test_read_metadata_from_mp4_freeform_custom_times(self, tmp_path, monkeypatch):
        """MP4 files can carry custom times under freeform atoms (mocked mutagen)."""
        import services.video.video_metadata as vm

        video_path = tmp_path / "test.mp4"
        video_path.write_bytes(b"")

        class FakeMP4:
            def __init__(self, _path):
                self.tags = {
                    vm.START_TIME_IN_MS_TAG: [b"1500"],
                    vm.END_TIME_IN_MS_TAG: [b"2500"],
                }
                self.info = None

        monkeypatch.setattr(vm, "MUTAGEN_AVAILABLE", True, raising=False)
        monkeypatch.setattr(vm, "MP4", FakeMP4, raising=False)

        metadata = vm.read_video_metadata(str(video_path), include_duration=False, check_nfo=False, include_thumbnail=False)
        assert metadata["start_time_in_ms"] == 1500
        assert metadata["end_time_in_ms"] == 2500

    def test_read_metadata_from_mp4_artists_tag(self, tmp_path, monkeypatch):
        """MP4 files can carry artists under the standard iTunes tag \xa9ART (mocked mutagen)."""
        import services.video.video_metadata as vm

        video_path = tmp_path / "artists.mp4"
        video_path.write_bytes(b"")

        class FakeMP4:
            def __init__(self, _path):
                self.tags = {
                    vm.ARTISTS_TAG: ["Artist One", "Artist Two"],
                }
                self.info = None

        monkeypatch.setattr(vm, "MUTAGEN_AVAILABLE", True, raising=False)
        monkeypatch.setattr(vm, "MP4", FakeMP4, raising=False)

        metadata = vm.read_video_metadata(str(video_path), include_duration=False, check_nfo=False, include_thumbnail=False)
        assert metadata["artist"] == "Artist One, Artist Two"

    def test_read_metadata_from_mp4_title_tag(self, tmp_path, monkeypatch):
        """MP4 files can carry title under the standard iTunes tag \xa9nam (mocked mutagen)."""
        import services.video.video_metadata as vm

        video_path = tmp_path / "title.mp4"
        video_path.write_bytes(b"")

        class FakeMP4:
            def __init__(self, _path):
                self.tags = {
                    vm.TITLE_TAG: ["Embedded Title"],
                }
                self.info = None

        monkeypatch.setattr(vm, "MUTAGEN_AVAILABLE", True, raising=False)
        monkeypatch.setattr(vm, "MP4", FakeMP4, raising=False)

        metadata = vm.read_video_metadata(str(video_path), include_duration=False, check_nfo=False, include_thumbnail=False)
        assert metadata["title"] == "Embedded Title"

    def test_read_metadata_from_mp4_tags_field_populates_tags(self, tmp_path, monkeypatch):
        """MP4 files can carry tags under a literal 'tags' field/key (mocked mutagen)."""
        import services.video.video_metadata as vm

        video_path = tmp_path / "tags.mp4"
        video_path.write_bytes(b"")

        class FakeMP4:
            def __init__(self, _path):
                self.tags = {
                    vm.MP4_TAGS_FIELD: ["Action, Adventure"],
                }
                self.info = None

        monkeypatch.setattr(vm, "MUTAGEN_AVAILABLE", True, raising=False)
        monkeypatch.setattr(vm, "MP4", FakeMP4, raising=False)

        metadata = vm.read_video_metadata(str(video_path), include_duration=False, check_nfo=False, include_thumbnail=False)
        assert metadata["tags"] == ["Action", "Adventure"]
    
    def test_find_nfo_file_exists(self):
        """Test finding an existing NFO file."""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as video_file:
            video_path = video_file.name
        
        nfo_path = os.path.splitext(video_path)[0] + '.nfo'
        
        # Create NFO file
        with open(nfo_path, 'w') as f:
            f.write('<?xml version="1.0"?><movie></movie>')
        
        try:
            found_nfo = find_nfo_file(video_path)
            assert found_nfo == nfo_path
        finally:
            os.unlink(video_path)
            if os.path.exists(nfo_path):
                os.unlink(nfo_path)
    
    def test_find_nfo_file_not_exists(self):
        """Test finding NFO file when it doesn't exist."""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as video_file:
            video_path = video_file.name
        
        try:
            found_nfo = find_nfo_file(video_path)
            assert found_nfo is None
        finally:
            os.unlink(video_path)


class TestVideoMetadataNfoWriting:
    def test_update_nfo_user_metadata_writes_custom_times(self):
        nfo_content = """<?xml version="1.0" encoding="UTF-8"?>
<movie>
    <title>Timed Movie</title>
    <userscore>5.0</userscore>
    <genre>Old</genre>
</movie>
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.nfo', delete=False) as f:
            f.write(nfo_content)
            nfo_path = f.name

        try:
            ok = update_nfo_user_metadata(
                nfo_path,
                user_rating=8.0,
                tags=['Action'],
                start_time_in_ms=1500,
                end_time_in_ms=2500,
            )
            assert ok is True

            metadata = parse_nfo_file(nfo_path)
            assert metadata['user_rating'] == 8.0
            assert metadata['tags'] == ['Action']
            assert metadata['start_time_in_ms'] == 1500
            assert metadata['end_time_in_ms'] == 2500
        finally:
            os.unlink(nfo_path)

    def test_update_nfo_user_metadata_removes_custom_times_when_none(self):
        nfo_content = """<?xml version="1.0" encoding="UTF-8"?>
<movie>
    <title>Timed Movie</title>
    <start_time_in_ms>1200</start_time_in_ms>
    <end_time_in_ms>3456</end_time_in_ms>
</movie>
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.nfo', delete=False) as f:
            f.write(nfo_content)
            nfo_path = f.name

        try:
            ok = update_nfo_user_metadata(
                nfo_path,
                user_rating=None,
                tags=[],
                start_time_in_ms=None,
                end_time_in_ms=None,
            )
            assert ok is True

            metadata = parse_nfo_file(nfo_path)
            assert 'start_time_in_ms' not in metadata
            assert 'end_time_in_ms' not in metadata
        finally:
            os.unlink(nfo_path)
