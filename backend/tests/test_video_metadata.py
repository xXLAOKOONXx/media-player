"""Tests for video metadata extraction from NFO files."""

import os
import tempfile
import pytest
from pathlib import Path

from video_metadata import parse_nfo_file, read_video_metadata, find_nfo_file


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
