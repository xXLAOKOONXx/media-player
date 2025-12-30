import os

from services.general.database_manager import DatabaseManager


def test_prefered_subtitle_presence_off_vs_missing(temp_dir):
    db_path = os.path.join(temp_dir, "test_media_player.db")
    db = DatabaseManager(db_path=db_path)

    user_id = db.create_user("test_user", None, "user")
    scope_type = "video"
    scope_key = "a" * 64

    exists, subtitle = db.get_prefered_subtitle_with_presence(
        user_id=user_id,
        scope_type=scope_type,
        scope_key=scope_key,
    )
    assert exists is False
    assert subtitle is None

    # Store "Off" (NULL)
    db.upsert_prefered_subtitle(
        user_id=user_id,
        scope_type=scope_type,
        scope_key=scope_key,
        subtitle=None,
    )

    exists, subtitle = db.get_prefered_subtitle_with_presence(
        user_id=user_id,
        scope_type=scope_type,
        scope_key=scope_key,
    )
    assert exists is True
    assert subtitle is None

    # Store an explicit subtitle track id
    db.upsert_prefered_subtitle(
        user_id=user_id,
        scope_type=scope_type,
        scope_key=scope_key,
        subtitle=3,
    )

    exists, subtitle = db.get_prefered_subtitle_with_presence(
        user_id=user_id,
        scope_type=scope_type,
        scope_key=scope_key,
    )
    assert exists is True
    assert subtitle == 3
