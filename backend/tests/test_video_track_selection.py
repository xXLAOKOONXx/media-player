import services.video.video_playback_controller as video_playback_controller
from services.video.video_playback_controller import VideoPlaybackController


def test_video_set_audio_track_state_only(monkeypatch):
    monkeypatch.setattr(video_playback_controller, "MPV_AVAILABLE", False, raising=False)
    controller = VideoPlaybackController(video_config={"fullscreen": True, "preferred_screen": None})
    controller.player = None
    controller.video_available = False

    assert controller.set_audio_track(2) is True
    status = controller.get_status()
    assert status.get('current_audio_track_id') == 2


def test_video_set_subtitle_track_off_state_only(monkeypatch):
    monkeypatch.setattr(video_playback_controller, "MPV_AVAILABLE", False, raising=False)
    controller = VideoPlaybackController(video_config={"fullscreen": True, "preferred_screen": None})
    controller.player = None
    controller.video_available = False

    assert controller.set_subtitle_track(-1) is True
    status = controller.get_status()
    assert status.get('current_subtitle_track_id') == -1


def test_video_default_forced_subtitle_selected_when_lang_matches(monkeypatch):
    monkeypatch.setattr(video_playback_controller, "MPV_AVAILABLE", False, raising=False)

    class FakeMpv:
        def __init__(self):
            self.aid = 1
            self.sid = 'no'
            self.track_list = [
                {'id': 1, 'type': 'audio', 'lang': 'en', 'selected': True},
                {'id': 3, 'type': 'sub', 'lang': 'en', 'title': None, 'metadata': {'name': 'English Forced'}, 'selected': False},
            ]

    controller = VideoPlaybackController(video_config={"fullscreen": True, "preferred_screen": None})
    controller.player = FakeMpv()
    controller.video_available = True

    controller._maybe_select_default_forced_subtitle()
    assert controller.selected_subtitle_track_id == 3
    assert controller.player.sid == 3


def test_video_default_forced_subtitle_not_selected_if_user_chose_subtitles(monkeypatch):
    monkeypatch.setattr(video_playback_controller, "MPV_AVAILABLE", False, raising=False)

    class FakeMpv:
        def __init__(self):
            self.aid = 1
            self.sid = 'no'
            self.track_list = [
                {'id': 1, 'type': 'audio', 'lang': 'en', 'selected': True},
                {'id': 3, 'type': 'sub', 'lang': 'en', 'title': 'Forced', 'metadata': {'name': 'Forced'}, 'selected': False},
            ]

    controller = VideoPlaybackController(video_config={"fullscreen": True, "preferred_screen": None})
    controller.player = FakeMpv()
    controller.video_available = True

    assert controller.set_subtitle_track(-1) is True
    controller._maybe_select_default_forced_subtitle()
    assert controller.selected_subtitle_track_id == -1
    assert controller.player.sid == 'no'
