"""Tests that video library listings include playback stats fields."""

import os
import sqlite3
import tempfile
import sys
import types


def test_video_library_videos_includes_playcount_and_last_played(monkeypatch):
    # Import here so monkeypatches can be applied after module init.
    if 'bcrypt' not in sys.modules:
        sys.modules['bcrypt'] = types.SimpleNamespace(
            gensalt=lambda: b'salt',
            hashpw=lambda _password, _salt: b'hash',
            checkpw=lambda _password, _password_hash: True,
        )
    import app as app_module

    # Keep the test deterministic by fixing the promotion score calculation.
    monkeypatch.setattr(app_module, 'calculate_promotion_score', lambda **_kwargs: 1234.5)

    with tempfile.TemporaryDirectory() as temp_dir:
        video_path = os.path.join(temp_dir, "movie.mp4")
        open(video_path, "wb").close()

        # Patch config so the endpoint can find library_id=1.
        monkeypatch.setattr(
            app_module,
            "load_config",
            lambda: {
                "video_libraries": [
                    {"id": 1, "name": "Test", "path": temp_dir, "recursive": False}
                ]
            },
        )

        # Patch video manager to return a deterministic video list.
        def fake_get_video_files(path, recursive=False, folder_id=None, force_refresh=False):
            assert path == temp_dir
            assert folder_id == 1
            return [
                {
                    "path": video_path,
                    "name": "movie.mp4",
                    "title": "movie",
                }
            ]

        monkeypatch.setattr(app_module.video_manager, "get_video_files", fake_get_video_files)

        # Create an isolated stats DB with known timestamps.
        stats_dir = os.path.join(temp_dir, "stats")
        os.makedirs(stats_dir, exist_ok=True)
        from services.general.stats_manager import StatsManager

        manager = StatsManager(stats_dir)
        assert manager.is_initialized()

        conn = sqlite3.connect(manager.db_path, timeout=5.0)
        cursor = conn.cursor()
        col = manager._get_path_column_name()

        cursor.execute(
            f"INSERT INTO media_stats (timestamp, {col}, username) VALUES (?, ?, ?)",
            (1000.0, video_path, "alice"),
        )
        cursor.execute(
            f"INSERT INTO media_stats (timestamp, {col}, username) VALUES (?, ?, ?)",
            (2000.0, video_path, "bob"),
        )
        conn.commit()
        conn.close()

        monkeypatch.setattr(app_module, "stats_manager", manager)

        client = app_module.app.test_client()
        resp = client.get("/api/video/libraries/1/videos")
        assert resp.status_code == 200

        videos = resp.get_json()
        assert isinstance(videos, list)
        assert len(videos) == 1

        video = videos[0]
        assert video["path"] == video_path
        assert video["playcount"] == 2
        assert video["last_played"] == 2000.0
        assert video["promotion_score"] == 1234.5
