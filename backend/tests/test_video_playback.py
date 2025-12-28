import video_playback_controller
from video_playback_controller import VideoPlaybackController


def test_video_play_controller_play_state_only_mode(tmp_path, monkeypatch):
    """Regression test: ensure play() actually starts playback.

    A previous refactor accidentally introduced a duplicate/incomplete play() method
    that overrode the real implementation, causing play() to do nothing and return None.

    This test forces "no video player" mode and verifies play() returns True and
    toggles state when a playlist is present.
    """

    # Force no-video mode so the test does not depend on mpv being installed.
    monkeypatch.setattr(video_playback_controller, "MPV_AVAILABLE", False, raising=False)

    controller = VideoPlaybackController(video_config={"fullscreen": True, "preferred_screen": None})

    # Ensure we are in state-only mode.
    controller.player = None
    controller.video_available = False

    video_path = tmp_path / "test.mp4"
    video_path.write_bytes(b"")

    controller.current_playlist = [
        {
            "path": str(video_path),
            "title": "test.mp4",
            "duration": 10.0,
            "start_time": None,
            "end_time": None,
        }
    ]
    controller.current_track_index = 0

    assert controller.play() is True
    assert controller.is_playing is True
    assert controller.is_paused is False
