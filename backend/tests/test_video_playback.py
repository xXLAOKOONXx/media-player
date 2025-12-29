import services.video.video_playback_controller as video_playback_controller
from services.video.video_playback_controller import VideoPlaybackController


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


def test_add_tracks_applies_custom_times_from_metadata(tmp_path, monkeypatch):
    """When adding videos, start/end times should be derived from metadata ms fields."""
    monkeypatch.setattr(video_playback_controller, "MPV_AVAILABLE", False, raising=False)

    # Mock metadata extraction to simulate MP4 freeform tags / NFO ms fields.
    def fake_read_video_metadata(_path, **_kwargs):
        return {"start_time_in_ms": 1000, "end_time_in_ms": 5000}

    monkeypatch.setattr(video_playback_controller, "read_video_metadata", fake_read_video_metadata, raising=False)

    controller = VideoPlaybackController(video_config={"fullscreen": True, "preferred_screen": None})
    controller.player = None
    controller.video_available = False

    video_path = tmp_path / "timed.mp4"
    video_path.write_bytes(b"")

    controller.add_tracks([str(video_path)])
    assert len(controller.current_playlist) == 1
    track = controller.current_playlist[0]
    assert track["start_time"] == 1.0
    assert track["end_time"] == 5.0


def test_custom_end_time_advances_to_next_track(tmp_path, monkeypatch):
    """If end_time is reached, playback should advance to the next track."""
    monkeypatch.setattr(video_playback_controller, "MPV_AVAILABLE", False, raising=False)

    controller = VideoPlaybackController(video_config={"fullscreen": True, "preferred_screen": None})
    controller.player = None
    controller.video_available = False

    p1 = tmp_path / "a.mp4"
    p2 = tmp_path / "b.mp4"
    p1.write_bytes(b"")
    p2.write_bytes(b"")

    controller.current_playlist = [
        {"path": str(p1), "title": "a.mp4", "duration": 10.0, "start_time": None, "end_time": 1.0},
        {"path": str(p2), "title": "b.mp4", "duration": 10.0, "start_time": None, "end_time": None},
    ]
    controller.original_playlist = list(controller.current_playlist)
    controller.current_track_index = 0
    controller.is_playing = True
    controller.is_paused = False

    controller.current_position = 1.05
    controller._check_custom_end_time()

    assert controller.current_track_index == 1
