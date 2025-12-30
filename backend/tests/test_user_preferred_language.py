import os

from services.general.database_manager import DatabaseManager


def test_user_preferred_language_roundtrip(temp_dir):
    db_path = os.path.join(temp_dir, 'test_media_player.db')
    db = DatabaseManager(db_path=db_path)

    user_id = db.create_user('alice', None, 'custom')
    assert user_id is not None

    user = db.get_user_by_id(user_id)
    assert user is not None
    assert user.get('preferred_language') in (None, 'eng')

    db.update_user_preferred_language(user_id, 'deu')

    user2 = db.get_user_by_id(user_id)
    assert user2 is not None
    assert user2.get('preferred_language') == 'deu'
