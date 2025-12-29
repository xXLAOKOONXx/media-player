"""Unit tests for audio stats media_id recording."""

import hashlib
import os
import time


class DummyStats:
    def __init__(self):
        self.calls = []

    def is_initialized(self):
        return True

    def record_media_stat(self, file_path, username, media_id=None):
        self.calls.append((file_path, username, media_id))
        return True


def test_audio_stats_records_media_id(tmp_path, monkeypatch):
    import services.audio.playback_controller as audio_playback_controller
    from services.audio.playback_controller import PlaybackController

    # Avoid initializing pygame mixer in unit test.
    monkeypatch.setattr(audio_playback_controller, "PYGAME_AVAILABLE", False, raising=False)

    controller = PlaybackController(stats_manager=DummyStats())

    track_path = tmp_path / "song.mp3"
    track_path.write_bytes(b"")

    controller.current_playlist = [{
        "path": str(track_path),
        "duration": 100.0,
    }]
    controller.current_track_index = 0
    controller.current_username = "alice"

    controller.track_start_time = time.time() - 60  # exceed 50% threshold
    controller.total_pause_duration = 0

    controller._check_and_record_stats()

    assert controller.stats_recorded is True
    assert controller.stats_manager.calls

    called_path, called_user, called_media_id = controller.stats_manager.calls[0]
    assert called_path == str(track_path)
    assert called_user == "alice"

    expected_media_id = hashlib.sha256(os.path.normpath(str(track_path)).encode("utf-8", errors="replace")).hexdigest()
    assert called_media_id == expected_media_id
