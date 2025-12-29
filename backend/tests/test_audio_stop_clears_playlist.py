def test_audio_stop_and_clear_playlist_empties_queue(monkeypatch):
    import os
    import sys

    # Add backend to path (matches other audio tests in this suite)
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

    import services.audio.playback_controller as audio_playback_controller
    from services.audio.playback_controller import PlaybackController

    # Ensure we run in state-only mode (no external player).
    monkeypatch.setattr(audio_playback_controller, "PYGAME_AVAILABLE", False, raising=False)

    controller = PlaybackController()

    controller.current_playlist = [
        {"path": "a.mp3", "title": "a.mp3", "duration": 10.0},
        {"path": "b.mp3", "title": "b.mp3", "duration": 10.0},
    ]
    controller.original_playlist = list(controller.current_playlist)
    controller.current_track_index = 1
    controller.is_playing = True

    assert controller.stop_and_clear_playlist() is True
    assert controller.current_playlist == []
    assert controller.original_playlist == []
    assert controller.current_track_index == 0
    assert controller.is_playing is False
