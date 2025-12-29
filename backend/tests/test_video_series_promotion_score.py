"""Tests that series tree listings include promotion_score fields on nested videos."""

import sys
import types


def test_video_library_series_includes_promotion_score(monkeypatch):
    # Import here so monkeypatches can be applied after module init.
    if 'bcrypt' not in sys.modules:
        sys.modules['bcrypt'] = types.SimpleNamespace(
            gensalt=lambda: b'salt',
            hashpw=lambda _password, _salt: b'hash',
            checkpw=lambda _password, _password_hash: True,
        )

    import app as app_module

    # Keep deterministic.
    monkeypatch.setattr(app_module, 'calculate_promotion_score', lambda **_kwargs: 9.9)

    monkeypatch.setattr(
        app_module,
        'load_config',
        lambda: {
            'video_libraries': [
                {'id': 1, 'name': 'Test', 'path': 'C:/tmp', 'recursive': True}
            ]
        },
    )

    def fake_build_series_tree(_path, folder_id=None, force_refresh=False):
        assert folder_id == 1
        assert force_refresh is True
        return [
            {
                'id': 'series-1',
                'full_path': 'C:/tmp/Series1',
                'title': 'Series 1',
                'tags': ['TagA'],
                'videos': [
                    {'path': 'C:/tmp/Series1/ep0.mp4', 'name': 'ep0.mp4', 'title': 'EP0'}
                ],
                'seasons': [
                    {
                        'id': 'season-1',
                        'full_path': 'C:/tmp/Series1/S01',
                        'title': 'Season 1',
                        'videos': [
                            {'path': 'C:/tmp/Series1/S01/ep1.mp4', 'name': 'ep1.mp4', 'title': 'EP1'}
                        ],
                    }
                ],
            }
        ]

    monkeypatch.setattr(app_module.video_manager, 'build_series_tree', fake_build_series_tree)

    # Make stats optional/no-op.
    monkeypatch.setattr(app_module, 'stats_manager', None)

    client = app_module.app.test_client()

    resp = client.get('/api/video/libraries/1/series?refresh=true')
    assert resp.status_code == 200

    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) == 1

    series = data[0]
    assert series['title'] == 'Series 1'

    series_videos = series.get('videos') or []
    assert series_videos[0]['promotion_score'] == 9.9

    seasons = series.get('seasons') or []
    season_videos = seasons[0].get('videos') or []
    assert season_videos[0]['promotion_score'] == 9.9
