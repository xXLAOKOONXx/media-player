"""Test that cached series tree properly includes videos in series and seasons."""

import os
import sys
import types
from pathlib import Path


def test_cached_series_tree_includes_videos(tmp_path: Path):
    """Test that get_cached_video_series_tree returns videos in series/seasons."""
    
    # Mock bcrypt before importing
    if 'bcrypt' not in sys.modules:
        sys.modules['bcrypt'] = types.SimpleNamespace(
            gensalt=lambda: b'salt',
            hashpw=lambda _password, _salt: b'hash',
            checkpw=lambda _password, _password_hash: True,
        )
    
    from services.video.video_cache import VideoCache
    from services.video.video_manager import VideoManager
    
    # Set up test directory structure
    lib_root = tmp_path / 'lib'
    series_dir = lib_root / 'MySeries'
    season_dir = series_dir / 'S01'
    season_dir.mkdir(parents=True)
    
    # Create test video files
    episode1_path = season_dir / 'S01E01.mkv'
    episode1_path.write_bytes(b'')
    
    series_root_video = series_dir / 'extras.mkv'
    series_root_video.write_bytes(b'')
    
    db_path = tmp_path / 'test_media.db'
    
    # Initialize VideoManager with cache
    vm = VideoManager(use_cache=False)
    vm.cache = VideoCache(str(db_path))
    
    # Register the folder
    folder_id = 1
    vm.cache.register_folder(folder_id, str(lib_root), recursive=True)
    
    # Build series tree (this simulates what happens during a fresh scan)
    series_tree = vm.build_series_tree(
        str(lib_root),
        folder_id=folder_id,
        force_refresh=True
    )
    
    # Verify the tree was built correctly
    assert len(series_tree) == 1
    series = series_tree[0]
    assert series['title'] == 'MySeries'
    assert len(series['videos']) == 1  # extras.mkv
    assert len(series['seasons']) == 1
    
    season = series['seasons'][0]
    assert len(season['videos']) == 1  # S01E01.mkv
    
    # Now cache the series tree (simulating what happens in the endpoint)
    vm.cache.cache_series_tree(folder_id, series_tree)
    
    # Retrieve from cache
    cached_tree = vm.cache.get_cached_series_tree(folder_id)
    
    # Verify the cached tree includes videos
    assert cached_tree is not None
    assert len(cached_tree) == 1
    
    cached_series = cached_tree[0]
    assert cached_series['title'] == 'MySeries'
    
    # This is the critical test: videos must be present in cached result
    assert len(cached_series['videos']) == 1, "Series root videos missing from cache"
    assert cached_series['videos'][0]['path'] == str(series_root_video)
    
    assert len(cached_series['seasons']) == 1
    cached_season = cached_series['seasons'][0]
    assert len(cached_season['videos']) == 1, "Season videos missing from cache"
    assert cached_season['videos'][0]['path'] == str(episode1_path)


def test_cache_series_tree_updates_video_links(tmp_path: Path):
    """Test that cache_series_tree properly links videos to series/seasons in DB."""
    
    # Mock bcrypt before importing
    if 'bcrypt' not in sys.modules:
        sys.modules['bcrypt'] = types.SimpleNamespace(
            gensalt=lambda: b'salt',
            hashpw=lambda _password, _salt: b'hash',
            checkpw=lambda _password, _password_hash: True,
        )
    
    from services.video.video_cache import VideoCache
    from services.video.video_manager import VideoManager
    
    # Set up test directory structure
    lib_root = tmp_path / 'lib'
    series_dir = lib_root / 'TestSeries'
    season_dir = series_dir / 'Season 01'
    season_dir.mkdir(parents=True)
    
    episode_path = season_dir / 'episode.mkv'
    episode_path.write_bytes(b'')
    
    db_path = tmp_path / 'test_media.db'
    
    vm = VideoManager(use_cache=False)
    vm.cache = VideoCache(str(db_path))
    
    folder_id = 1
    vm.cache.register_folder(folder_id, str(lib_root), recursive=True)
    
    # First, cache videos without series tree
    videos = vm.get_video_files(
        str(lib_root),
        recursive=True,
        folder_id=folder_id,
        force_refresh=True
    )
    
    assert len(videos) > 0
    
    # Now build and cache the series tree
    series_tree = vm.build_series_tree(
        str(lib_root),
        folder_id=folder_id,
        force_refresh=False  # Use cached videos
    )
    
    # Cache the series tree (this should update video links)
    vm.cache.cache_series_tree(folder_id, series_tree)
    
    # Retrieve and verify
    cached_tree = vm.cache.get_cached_series_tree(folder_id)
    
    assert cached_tree is not None
    assert len(cached_tree) == 1
    assert len(cached_tree[0]['seasons']) == 1
    assert len(cached_tree[0]['seasons'][0]['videos']) == 1
    
    # Verify the video path matches
    cached_video = cached_tree[0]['seasons'][0]['videos'][0]
    assert cached_video['path'] == str(episode_path)
