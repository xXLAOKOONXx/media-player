"""Tests for thumbnail extraction and storage."""

import os
import tempfile
from pathlib import Path

from video_metadata import (
    find_poster_file,
    extract_embedded_thumbnail,
    read_thumbnail_data,
    read_video_metadata
)


class TestThumbnailExtraction:
    """Test thumbnail extraction from various sources."""
    
    def test_find_poster_file_exists(self):
        """Test finding an existing poster file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a video file
            video_path = os.path.join(temp_dir, 'movie.mp4')
            Path(video_path).touch()
            
            # Create poster file
            poster_path = os.path.join(temp_dir, 'movie-poster.jpg')
            with open(poster_path, 'wb') as f:
                f.write(b'fake image data')
            
            found_poster = find_poster_file(video_path)
            assert found_poster == poster_path
    
    def test_find_poster_file_not_exists(self):
        """Test when poster file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = os.path.join(temp_dir, 'movie.mp4')
            Path(video_path).touch()
            
            found_poster = find_poster_file(video_path)
            assert found_poster is None
    
    def test_read_thumbnail_from_poster_file(self):
        """Test reading thumbnail from poster file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = os.path.join(temp_dir, 'movie.mp4')
            Path(video_path).touch()
            
            # Create poster file with test data
            poster_path = os.path.join(temp_dir, 'movie-poster.jpg')
            test_data = b'\xff\xd8\xff\xe0\x00\x10JFIF'  # JPEG magic bytes
            with open(poster_path, 'wb') as f:
                f.write(test_data)
            
            thumbnail_data, mime_type = read_thumbnail_data(video_path)
            
            assert thumbnail_data == test_data
            assert mime_type == 'image/jpeg'
    
    def test_read_thumbnail_no_sources(self):
        """Test when no thumbnail sources are available."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = os.path.join(temp_dir, 'movie.mp4')
            Path(video_path).touch()
            
            result = read_thumbnail_data(video_path)
            assert result is None
    
    def test_read_video_metadata_with_thumbnail(self):
        """Test reading video metadata including thumbnail."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = os.path.join(temp_dir, 'movie.mp4')
            Path(video_path).touch()
            
            # Create poster file
            poster_path = os.path.join(temp_dir, 'movie-poster.jpg')
            test_data = b'\xff\xd8\xff\xe0\x00\x10JFIF'
            with open(poster_path, 'wb') as f:
                f.write(test_data)
            
            metadata = read_video_metadata(
                video_path,
                include_duration=False,
                include_thumbnail=True
            )
            
            assert 'thumbnail' in metadata
            assert metadata['thumbnail'] == test_data
            assert metadata['thumbnail_mime_type'] == 'image/jpeg'
    
    def test_read_video_metadata_without_thumbnail(self):
        """Test reading metadata with thumbnail disabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = os.path.join(temp_dir, 'movie.mp4')
            Path(video_path).touch()
            
            # Create poster file (should be ignored)
            poster_path = os.path.join(temp_dir, 'movie-poster.jpg')
            with open(poster_path, 'wb') as f:
                f.write(b'test')
            
            metadata = read_video_metadata(
                video_path,
                include_duration=False,
                include_thumbnail=False
            )
            
            assert 'thumbnail' not in metadata
