from datetime import date

from services.general.promotion_score import calculate_promotion_score


def test_promotion_score_is_deterministic_for_same_inputs_and_day():
    today = date(2025, 12, 29)

    s1 = calculate_promotion_score(
        file_path='C:/media/movie.mp4',
        playcount=3,
        last_played=1735430400.0,  # epoch seconds (arbitrary)
        user_rating=7,
        today=today,
    )
    s2 = calculate_promotion_score(
        file_path='C:/media/movie.mp4',
        playcount=3,
        last_played=1735430400.0,
        user_rating=7,
        today=today,
    )

    assert s1 == s2


def test_promotion_score_changes_with_file_path_seed():
    today = date(2025, 12, 29)
    s1 = calculate_promotion_score(file_path='C:/media/a.mp4', today=today)
    s2 = calculate_promotion_score(file_path='C:/media/b.mp4', today=today)
    assert s1 != s2
