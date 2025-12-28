from video_playback_controller import VideoPlaybackController


class DummyStats:
    def __init__(self):
        self._initialized = True
        self.calls = []

    def is_initialized(self):
        return True

    def record_media_stat(self, file_path, username):
        self.calls.append((file_path, username))
        return True


def test_stats_check_handles_none_times(tmp_path):
    controller = VideoPlaybackController(video_config={"fullscreen": False}, stats_manager=DummyStats())
    controller.player = None
    controller.video_available = False

    # Prepare a fake video
    video_path = tmp_path / "clip.mp4"
    video_path.write_bytes(b"")

    controller.current_playlist = [{
        "path": str(video_path),
        "title": "clip.mp4",
        "duration": 100.0,
        "start_time": None,  # keys exist but are None
        "end_time": None,
    }]
    controller.current_track_index = 0
    controller.current_username = "alice"

    # Make elapsed time exceed threshold (50% of effective=duration=100 -> 50)
    import time
    controller.track_start_time = time.time() - 60
    controller.total_pause_duration = 0

    # Should not raise and should record once
    controller._check_and_record_stats()

    assert controller.stats_recorded is True
    assert controller.stats_manager.calls
    # Path should be the full file path now
    assert controller.stats_manager.calls[0][0] == str(video_path)
    assert controller.stats_manager.calls[0][1] == "alice"
