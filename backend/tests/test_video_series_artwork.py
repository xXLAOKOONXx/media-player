import hashlib
import os
from pathlib import Path

from services.video.video_cache import VideoCache
from services.video.video_manager import VideoManager


def _stable_tree_id(prefix: str, full_path: str) -> str:
    return f"{prefix}_{hashlib.sha1(os.path.normpath(full_path).lower().encode('utf-8', errors='ignore')).hexdigest()[:12]}"


def test_series_and_season_posters_are_used_and_cached(tmp_path: Path):
    lib_root = tmp_path / 'lib'
    series_dir = lib_root / 'MySeries'
    season_dir = series_dir / 'S01'
    season_dir.mkdir(parents=True)

    # Minimal dummy episode file.
    episode_path = season_dir / 'S01E01.mkv'
    episode_path.write_bytes(b'')

    # Series poster at SERIES/poster.jpg
    series_poster = series_dir / 'poster.jpg'
    series_poster.write_bytes(b'\xff\xd8\xff\xe0\x00\x10JFIF-series')

    # Season poster at SERIES/season01-poster.jpg
    season_poster = series_dir / 'season01-poster.jpg'
    season_poster.write_bytes(b'\xff\xd8\xff\xe0\x00\x10JFIF-season')

    db_path = tmp_path / 'media.db'

    vm = VideoManager(use_cache=False)
    vm.cache = VideoCache(str(db_path))

    video = {
        'path': str(episode_path),
        'name': episode_path.name,
        'title': 'S01E01',
        'series': 'MySeries',
        'season': 'S01',
        'media_id': '0' * 64,
        'has_thumbnail': False,
    }

    tree = vm._build_series_tree_from_videos(str(lib_root), [video])

    assert isinstance(tree, list) and len(tree) == 1

    expected_series_id = _stable_tree_id('ser', str(series_dir))
    expected_season_id = _stable_tree_id('sea', str(season_dir))

    assert tree[0]['id'] == expected_series_id
    assert tree[0]['cover'] == f"/api/video/thumbnail/by-art-id/{expected_series_id}"

    assert tree[0]['seasons'][0]['id'] == expected_season_id
    assert tree[0]['seasons'][0]['cover'] == f"/api/video/thumbnail/by-art-id/{expected_season_id}"

    series_bytes, series_mime = vm.cache.db.get_video_artwork_thumbnail(expected_series_id)
    assert series_bytes == series_poster.read_bytes()
    assert (series_mime or '').startswith('image/')

    season_bytes, season_mime = vm.cache.db.get_video_artwork_thumbnail(expected_season_id)
    assert season_bytes == season_poster.read_bytes()
    assert (season_mime or '').startswith('image/')
