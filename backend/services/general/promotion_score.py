"""Promotion score calculation.

This module provides a reusable scoring function that can be applied to both
audio tracks and video items.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional, Union


LastPlayedValue = Union[None, date, datetime, float, int, str]
UserRatingValue = Union[None, float, int, str]


def _coerce_date(value: LastPlayedValue) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value)).date()
        except Exception:
            return None
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        # Try ISO date first: YYYY-MM-DD
        try:
            return date.fromisoformat(s[:10])
        except Exception:
            return None
    return None


def _coerce_int(value: object) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        try:
            return int(float(s))
        except Exception:
            return None
    return None


def _coerce_float(value: UserRatingValue) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        try:
            return float(s)
        except Exception:
            return None
    return None


def calculate_promotion_score(
    *,
    file_path: str,
    playcount: object = None,
    last_played: LastPlayedValue = None,
    user_rating: UserRatingValue = None,
    today: Optional[date] = None,
) -> float:
    """Calculate a promotion score for a playable media item.

    The score is intentionally deterministic within a given day/week/month for a
    given file_path, while also incorporating recency, playcount and an optional
    user rating.

    Args:
        file_path: Stable identifier for the playable (typically absolute path).
        playcount: Number of plays.
        last_played: Last-played timestamp (date/datetime/epoch seconds/ISO string).
        user_rating: Optional user rating (expected 0-10).
        today: Override for deterministic testing.
    """

    score: float = 1000.0

    if today is None:
        today = date.today()

    safe_path = (file_path or '').strip()

    # Random components (deterministic by period).
    score += random.Random(f'{safe_path}_{today.year}_{today.month}').randint(0, 100)
    score += random.Random(f'{safe_path}_{today.year}_{today.month}_{today.isocalendar().week}').randint(0, 100)
    score += random.Random(
        f'{safe_path}_{today.year}_{today.month}_{today.isocalendar().week}_{today.isocalendar().weekday}'
    ).randint(0, 300)

    # Recency watched penalties.
    last_played_date = _coerce_date(last_played)
    if last_played_date is not None:
        time_past = today - last_played_date
        if time_past <= timedelta(days=0):
            score += -1000
        if time_past <= timedelta(days=1):
            score += -500
        if time_past <= timedelta(weeks=1):
            score += -300
        if time_past <= timedelta(days=30):
            score += -200
        if time_past <= timedelta(days=360):
            score += -100
        if time_past <= timedelta(days=720):
            score += -50
        if time_past <= timedelta(days=1800):
            score += -10

    # Private score (user rating).
    rating = _coerce_float(user_rating)
    if rating is not None:
        personal_score_factor = -2 if rating < 6 else 2
        try:
            score += 10 * personal_score_factor * math.pow(2, personal_score_factor * (rating - 6))
        except OverflowError:
            # If an extreme rating causes overflow, clamp to a large magnitude.
            score += 1e9 if personal_score_factor > 0 else -1e9

    # Multi-watched bonus.
    pc = _coerce_int(playcount)
    if pc is not None and pc > 0:
        if pc == 1:
            score += 10
        elif pc <= 2:
            score += 30
        elif pc <= 5:
            score += 60
        elif pc <= 10:
            score += 150
        else:
            score += 100 + (pc * 5)

    return float(score)
