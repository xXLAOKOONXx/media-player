"""Tests for the soft-refresh behavior of video libraries and music folders.

Soft refresh keeps the existing cache as-is and only adds newly-discovered
files. Files already registered in the cache are not re-processed and missing
files are not pruned.
"""

import os
import sys
import types
from pathlib import Path

# Ensure backend package is importable and bcrypt is stubbed for imports.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
if 'bcrypt' not in sys.modules:
    sys.modules['bcrypt'] = types.SimpleNamespace(
        gensalt=lambda: b'salt',
        hashpw=lambda _password, _salt: b'hash',
        checkpw=lambda _password, _password_hash: True,
    )


def test_video_soft_refresh_adds_new_and_keeps_existing(tmp_path: Path, monkeypatch):
    from services.video import video_manager as vm_module
    from services.video.video_cache import VideoCache
    from services.video.video_manager import VideoManager

    lib_root = tmp_path / 'lib'
    lib_root.mkdir()
    (lib_root / 'a.mkv').write_bytes(b'')

    db_path = tmp_path / 'test_media.db'
    vm = VideoManager(use_cache=False)
    vm.cache = VideoCache(str(db_path))

    folder_id = 1

    # Count metadata reads to verify cached files are not re-processed.
    real_read = vm_module.read_video_metadata
    calls = []

    def counting_read(path, *args, **kwargs):
        calls.append(os.path.normpath(path))
        return real_read(path, *args, **kwargs)

    monkeypatch.setattr(vm_module, 'read_video_metadata', counting_read)

    # Initial scan populates the cache with a.mkv.
    initial = vm.get_video_files(str(lib_root), recursive=False, folder_id=folder_id)
    assert len(initial) == 1
    assert calls == [os.path.normpath(str(lib_root / 'a.mkv'))]

    # Add a new file and bump the mtime of the existing one.
    (lib_root / 'b.mkv').write_bytes(b'')
    os.utime(lib_root / 'a.mkv', (10 ** 12, 10 ** 12))

    calls.clear()
    refreshed = vm.get_video_files(
        str(lib_root), recursive=False, folder_id=folder_id, soft_refresh=True
    )

    names = sorted(v['name'] for v in refreshed)
    assert names == ['a.mkv', 'b.mkv']
    # Only the brand-new file should have its metadata read; the existing,
    # already-cached file must be kept as-is even though its mtime changed.
    assert calls == [os.path.normpath(str(lib_root / 'b.mkv'))]


def test_video_soft_refresh_keeps_missing_files(tmp_path: Path):
    from services.video.video_cache import VideoCache
    from services.video.video_manager import VideoManager

    lib_root = tmp_path / 'lib'
    lib_root.mkdir()
    (lib_root / 'a.mkv').write_bytes(b'')
    (lib_root / 'b.mkv').write_bytes(b'')

    db_path = tmp_path / 'test_media.db'
    vm = VideoManager(use_cache=False)
    vm.cache = VideoCache(str(db_path))
    folder_id = 1

    initial = vm.get_video_files(str(lib_root), recursive=False, folder_id=folder_id)
    assert len(initial) == 2

    # Remove one file, then soft refresh: cache should keep it.
    os.remove(lib_root / 'b.mkv')
    vm.get_video_files(
        str(lib_root), recursive=False, folder_id=folder_id, soft_refresh=True
    )

    # A normal (cache-backed) read must still list the removed file, proving
    # the soft refresh kept the current cache as-is.
    cached = vm.get_video_files(str(lib_root), recursive=False, folder_id=folder_id)
    names = sorted(v['name'] for v in cached)
    assert names == ['a.mkv', 'b.mkv']


def test_music_soft_refresh_adds_new_and_keeps_existing(tmp_path: Path):
    import glob
    import shutil
    from services.audio.music_cache import MusicCache
    from services.audio.music_manager import MusicManager

    example_dir = Path(__file__).parent.parent.parent / 'examples' / 'example_audio'
    sources = sorted(glob.glob(str(example_dir / '*.mp3')))
    if len(sources) < 2:
        import pytest
        pytest.skip('Need at least two example audio files')

    music_dir = tmp_path / 'music'
    music_dir.mkdir()
    shutil.copy(sources[0], music_dir / 'track1.mp3')

    db_path = tmp_path / 'test_media.db'
    mm = MusicManager(use_cache=False)
    mm.cache = MusicCache(str(db_path))
    folder_id = 1

    initial = mm.get_audio_files(str(music_dir), recursive=False, folder_id=folder_id)
    assert len(initial) == 1

    # Add a new track, ensure metadata is not re-read for the existing one.
    shutil.copy(sources[1], music_dir / 'track2.mp3')

    scanned = []
    real_scan = mm._scan_audio_files

    def spy_scan(path, recursive=False, include_duration=False, skip_paths=None):
        scanned.append(set(skip_paths or set()))
        return real_scan(path, recursive, include_duration=include_duration, skip_paths=skip_paths)

    mm._scan_audio_files = spy_scan

    refreshed = mm.get_audio_files(
        str(music_dir), recursive=False, folder_id=folder_id, soft_refresh=True
    )
    names = sorted(t['name'] for t in refreshed)
    assert names == ['track1.mp3', 'track2.mp3']
    # The already-cached track's path must be passed as a skip path.
    assert scanned and os.path.normpath(str(music_dir / 'track1.mp3')) in scanned[0]
