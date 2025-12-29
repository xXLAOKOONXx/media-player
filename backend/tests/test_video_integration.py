"""Integration tests for video metadata caching."""

import os
import tempfile
import shutil
from pathlib import Path

from services.video.video_manager import VideoManager
from services.general.database_manager import DatabaseManager


class TestVideoMetadataIntegration:
    """Test full integration of video metadata caching."""
    
    def test_scan_and_cache_video_with_nfo(self):
        """Test scanning a video folder with NFO files and caching metadata."""
        # Create temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a video file
            video_path = os.path.join(temp_dir, 'test_video.mp4')
            Path(video_path).touch()
            
            # Create accompanying NFO file
            nfo_path = os.path.join(temp_dir, 'test_video.nfo')
            nfo_content = """<?xml version="1.0" encoding="UTF-8"?>
<movie>
    <title>Test Movie Title</title>
    <artist>Director Name</artist>
    <plot>This is a test movie plot description.</plot>
    <premiered>2023-12-15</premiered>
    <Genre>Action</Genre>
    <Genre>Sci-Fi</Genre>
    <userscore>8.5</userscore>
    <thumb>https://example.com/poster.jpg</thumb>
</movie>
"""
            with open(nfo_path, 'w') as f:
                f.write(nfo_content)

            # Create a poster image that should be cached as thumbnail bytes
            poster_path = os.path.join(temp_dir, 'test_video-poster.jpg')
            poster_bytes = b'\xff\xd8\xff\xe0\x00\x10JFIF'  # JPEG magic bytes
            with open(poster_path, 'wb') as f:
                f.write(poster_bytes)
            
            # Create temporary database
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as db_file:
                db_path = db_file.name
            
            try:
                # Initialize video manager with caching
                db_manager = DatabaseManager(db_path)
                video_manager = VideoManager(use_cache=True)
                video_manager.cache = type('obj', (object,), {
                    'db': db_manager,
                    'register_folder': db_manager.register_video_folder,
                    'cache_videos': db_manager.cache_videos,
                    'get_cached_videos': db_manager.get_cached_videos,
                })()
                
                folder_id = 1
                
                # First scan - should read from filesystem and NFO
                videos = video_manager.get_video_files(
                    temp_dir,
                    recursive=False,
                    folder_id=folder_id,
                    force_refresh=True
                )
                
                assert len(videos) == 1
                video = videos[0]
                
                # Verify basic fields
                assert video['name'] == 'test_video.mp4'
                assert video['path'] == video_path
                
                # Verify metadata from NFO
                assert video['title'] == 'Test Movie Title'
                assert video['artist'] == 'Director Name'
                assert video['description'] == 'This is a test movie plot description.'
                assert video['premiere_date'] == '2023-12-15'
                assert video['user_rating'] == 8.5
                assert video['thumbnail_url'] == 'https://example.com/poster.jpg'
                assert video['has_thumbnail'] is True
                assert 'media_id' in video
                assert isinstance(video['media_id'], str)
                assert len(video['media_id']) > 0
                assert 'tags' in video
                assert 'Action' in video['tags']
                assert 'Sci-Fi' in video['tags']
                
                # Second scan - should read from cache
                cached_videos = video_manager.get_video_files(
                    temp_dir,
                    recursive=False,
                    folder_id=folder_id,
                    force_refresh=False
                )
                
                assert len(cached_videos) == 1
                cached_video = cached_videos[0]
                
                # Verify cached data matches
                assert cached_video['title'] == video['title']
                assert cached_video['artist'] == video['artist']
                assert cached_video['description'] == video['description']
                assert cached_video['premiere_date'] == video['premiere_date']
                assert cached_video['user_rating'] == video['user_rating']
                assert cached_video['thumbnail_url'] == video['thumbnail_url']
                assert cached_video['has_thumbnail'] is True
                assert cached_video['tags'] == video['tags']

                # Cached videos should have a stable identifier for URL-based requests
                assert 'media_id' in cached_video
                assert isinstance(cached_video['media_id'], str)
                assert len(cached_video['media_id']) > 0
                assert cached_video['media_id'] == video['media_id']

                # Verify thumbnail bytes are stored in DB and retrievable via cache API
                thumb_bytes, thumb_mime = db_manager.get_video_thumbnail(video_path)
                assert thumb_bytes == poster_bytes
                assert thumb_mime == 'image/jpeg'

                # Verify thumbnail is retrievable by media_id (stable identifier)
                mid_bytes, mid_mime = db_manager.get_video_thumbnail_by_media_id(cached_video['media_id'])
                assert mid_bytes == poster_bytes
                assert mid_mime == 'image/jpeg'
                
            finally:
                # Cleanup
                if os.path.exists(db_path):
                    os.unlink(db_path)
    
    def test_scan_video_without_nfo(self):
        """Test scanning a video without NFO file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a video file without NFO
            video_path = os.path.join(temp_dir, 'simple_video.mp4')
            Path(video_path).touch()
            
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as db_file:
                db_path = db_file.name
            
            try:
                db_manager = DatabaseManager(db_path)
                video_manager = VideoManager(use_cache=True)
                video_manager.cache = type('obj', (object,), {
                    'db': db_manager,
                    'register_folder': db_manager.register_video_folder,
                    'cache_videos': db_manager.cache_videos,
                    'get_cached_videos': db_manager.get_cached_videos,
                })()
                
                folder_id = 2
                
                videos = video_manager.get_video_files(
                    temp_dir,
                    recursive=False,
                    folder_id=folder_id,
                    force_refresh=True
                )
                
                assert len(videos) == 1
                video = videos[0]
                
                # Should have basic info
                assert video['name'] == 'simple_video.mp4'
                assert video['path'] == video_path
                assert video['title'] == 'simple_video'  # Default from filename
                
                # New metadata fields should be None or empty
                assert video.get('artist') is None or video.get('artist') == ''
                assert video.get('description') is None or video.get('description') == ''
                assert video.get('tags', []) == []
                
            finally:
                if os.path.exists(db_path):
                    os.unlink(db_path)
    
    def test_multiple_videos_with_mixed_metadata(self):
        """Test scanning multiple videos with some having NFO files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create first video with NFO
            video1_path = os.path.join(temp_dir, 'movie1.mp4')
            Path(video1_path).touch()
            nfo1_path = os.path.join(temp_dir, 'movie1.nfo')
            with open(nfo1_path, 'w') as f:
                f.write("""<?xml version="1.0" encoding="UTF-8"?>
<movie>
    <title>Movie One</title>
    <Genre>Drama</Genre>
</movie>
""")
            
            # Create second video without NFO
            video2_path = os.path.join(temp_dir, 'movie2.mp4')
            Path(video2_path).touch()
            
            # Create third video with NFO
            video3_path = os.path.join(temp_dir, 'movie3.mkv')
            Path(video3_path).touch()
            nfo3_path = os.path.join(temp_dir, 'movie3.nfo')
            with open(nfo3_path, 'w') as f:
                f.write("""<?xml version="1.0" encoding="UTF-8"?>
<movie>
    <title>Movie Three</title>
    <userscore>9.2</userscore>
</movie>
""")
            
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as db_file:
                db_path = db_file.name
            
            try:
                db_manager = DatabaseManager(db_path)
                video_manager = VideoManager(use_cache=True)
                video_manager.cache = type('obj', (object,), {
                    'db': db_manager,
                    'register_folder': db_manager.register_video_folder,
                    'cache_videos': db_manager.cache_videos,
                    'get_cached_videos': db_manager.get_cached_videos,
                })()
                
                folder_id = 3
                
                videos = video_manager.get_video_files(
                    temp_dir,
                    recursive=False,
                    folder_id=folder_id,
                    force_refresh=True
                )
                
                assert len(videos) == 3
                
                # Find specific videos
                movie1 = next(v for v in videos if v['name'] == 'movie1.mp4')
                movie2 = next(v for v in videos if v['name'] == 'movie2.mp4')
                movie3 = next(v for v in videos if v['name'] == 'movie3.mkv')
                
                # Verify movie1 has NFO metadata
                assert movie1['title'] == 'Movie One'
                assert 'Drama' in movie1.get('tags', [])
                
                # Verify movie2 has no metadata
                assert movie2['title'] == 'movie2'  # Default from filename
                
                # Verify movie3 has NFO metadata
                assert movie3['title'] == 'Movie Three'
                assert movie3['user_rating'] == 9.2
                
            finally:
                if os.path.exists(db_path):
                    os.unlink(db_path)
