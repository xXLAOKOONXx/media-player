"""Integration test for /api/video/libraries/<id>/series endpoint with cache."""

import sys
import types
from pathlib import Path


def test_series_endpoint_with_cache_returns_videos(tmp_path: Path, monkeypatch):
    """Test that /api/video/libraries/<id>/series returns videos when using cache."""
    
    # Mock bcrypt before importing app
    if 'bcrypt' not in sys.modules:
        sys.modules['bcrypt'] = types.SimpleNamespace(
            gensalt=lambda: b'salt',
            hashpw=lambda _password, _salt: b'hash',
            checkpw=lambda _password, _password_hash: True,
        )
    
    import app as app_module
    from services.video.video_cache import VideoCache
    from services.video.video_manager import VideoManager
    
    # Set up test directory structure
    lib_root = tmp_path / 'TestLibrary'
    series_dir = lib_root / 'AwesomeSeries'
    season_dir = series_dir / 'Season 1'
    season_dir.mkdir(parents=True)
    
    # Create test videos
    ep1_path = season_dir / 'S01E01.mkv'
    ep1_path.write_bytes(b'')
    
    ep2_path = season_dir / 'S01E02.mkv'
    ep2_path.write_bytes(b'')
    
    extras_path = series_dir / 'behind-the-scenes.mkv'
    extras_path.write_bytes(b'')
    
    db_path = tmp_path / 'media.db'
    
    # Configure the app with test library
    monkeypatch.setattr(
        app_module,
        'load_config',
        lambda: {
            'video_libraries': [
                {'id': 6, 'name': 'Test Library', 'path': str(lib_root), 'recursive': True}
            ]
        },
    )
    
    # Set up VideoManager with cache
    vm = VideoManager(use_cache=False)
    vm.cache = VideoCache(str(db_path))
    vm.cache.register_folder(6, str(lib_root), recursive=True)
    
    # Replace the global video_manager
    monkeypatch.setattr(app_module, 'video_manager', vm)
    
    # Make stats optional
    monkeypatch.setattr(app_module, 'stats_manager', None)
    
    client = app_module.app.test_client()
    
    # First request: forces a full scan and caches everything
    resp1 = client.get('/api/video/libraries/6/series?refresh=true')
    assert resp1.status_code == 200
    data1 = resp1.get_json()
    
    assert isinstance(data1, list)
    assert len(data1) == 1
    
    series1 = data1[0]
    assert series1['title'] == 'AwesomeSeries'
    assert len(series1['videos']) == 1, "First request: series videos missing"
    assert series1['videos'][0]['name'] == 'behind-the-scenes.mkv'
    
    assert len(series1['seasons']) == 1
    season1 = series1['seasons'][0]
    assert len(season1['videos']) == 2, "First request: season videos missing"
    
    # Second request: should use cache (no refresh parameter)
    # This is where the bug would manifest before the fix
    resp2 = client.get('/api/video/libraries/6/series')
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    
    assert isinstance(data2, list)
    assert len(data2) == 1
    
    series2 = data2[0]
    assert series2['title'] == 'AwesomeSeries'
    
    # Critical assertions: cached response must include videos
    assert len(series2['videos']) == 1, "Cached response: series videos missing!"
    assert series2['videos'][0]['name'] == 'behind-the-scenes.mkv'
    
    assert len(series2['seasons']) == 1
    season2 = series2['seasons'][0]
    assert len(season2['videos']) == 2, "Cached response: season videos missing!"
    
    # Verify video names
    video_names = sorted([v['name'] for v in season2['videos']])
    assert video_names == ['S01E01.mkv', 'S01E02.mkv']


def test_series_endpoint_cache_backfill_scenario(tmp_path: Path, monkeypatch):
    """Test that cache_series_tree properly links videos to series/seasons."""
    
    # Mock bcrypt
    if 'bcrypt' not in sys.modules:
        sys.modules['bcrypt'] = types.SimpleNamespace(
            gensalt=lambda: b'salt',
            hashpw=lambda _password, _salt: b'hash',
            checkpw=lambda _password, _password_hash: True,
        )
    
    import app as app_module
    from services.video.video_cache import VideoCache
    from services.video.video_manager import VideoManager
    
    # Set up test directory
    lib_root = tmp_path / 'Library'
    series_dir = lib_root / 'TestSeries'
    season_dir = series_dir / 'S01'
    season_dir.mkdir(parents=True)
    
    video_path = season_dir / 'episode.mkv'
    video_path.write_bytes(b'')
    
    db_path = tmp_path / 'media.db'
    
    monkeypatch.setattr(
        app_module,
        'load_config',
        lambda: {
            'video_libraries': [
                {'id': 1, 'name': 'Test', 'path': str(lib_root), 'recursive': True}
            ]
        },
    )
    
    vm = VideoManager(use_cache=False)
    vm.cache = VideoCache(str(db_path))
    
    monkeypatch.setattr(app_module, 'video_manager', vm)
    monkeypatch.setattr(app_module, 'stats_manager', None)
    
    client = app_module.app.test_client()
    
    # First request with refresh - builds and caches everything
    resp1 = client.get('/api/video/libraries/1/series?refresh=true')
    assert resp1.status_code == 200
    data1 = resp1.get_json()
    assert len(data1) == 1
    assert len(data1[0]['seasons'][0]['videos']) == 1
    
    # Second request WITHOUT refresh - should use cached series tree
    # This tests that the cache properly includes videos
    resp2 = client.get('/api/video/libraries/1/series')
    assert resp2.status_code == 200
    
    data2 = resp2.get_json()
    assert isinstance(data2, list)
    assert len(data2) == 1
    
    series = data2[0]
    assert len(series['seasons']) == 1
    
    # This is the critical test: videos must be present in cached response
    season = series['seasons'][0]
    assert len(season['videos']) == 1, "Videos missing from cached series tree!"
    assert season['videos'][0]['name'] == 'episode.mkv'
