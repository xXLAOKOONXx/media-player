"""Series/Season schema for videos.

This is an internal schema used to represent hierarchical video libraries when
folders are scanned recursively:
- Series: top-level folder inside the configured video library folder
- Season: second-level folder inside a Series folder

The frontend currently consumes flat video lists from `/api/video/libraries/<id>/videos`.
A dedicated endpoint can expose these structures without breaking existing UX.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Season:
    full_path: str
    title: str
    user_rating: float | None = None
    tags: list[str] = field(default_factory=list)
    artists: list[str] = field(default_factory=list)
    cover: str | None = None
    index_number: int | None = None
    videos: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            'full_path': self.full_path,
            'title': self.title,
            'user_rating': self.user_rating,
            'tags': self.tags,
            'artists': self.artists,
            'cover': self.cover,
            'index_number': self.index_number,
            'videos': self.videos,
        }


@dataclass
class Series:
    full_path: str
    title: str
    user_rating: float | None = None
    tags: list[str] = field(default_factory=list)
    artists: list[str] = field(default_factory=list)
    cover: str | None = None
    seasons: list[Season] = field(default_factory=list)
    videos: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            'full_path': self.full_path,
            'title': self.title,
            'user_rating': self.user_rating,
            'tags': self.tags,
            'artists': self.artists,
            'cover': self.cover,
            'seasons': [s.to_dict() for s in self.seasons],
            'videos': self.videos,
        }
