"""Video Manager

Handles video library management with metadata extraction from files and NFO files.
"""

import os
from pathlib import Path
import hashlib
import re
import time
import logging
from collections import defaultdict


from services.video.video_cache import VideoCache
from services.video.video_metadata import read_video_metadata
from services.video.video_metadata import find_nfo_file
from services.video.video_series_schema import Series, Season


logger = logging.getLogger(__name__)


class VideoManager:
    """Manages video libraries and tracks"""
    
    # Supported video file extensions
    VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg'}
    
    def __init__(self, use_cache=True):
        self.cache = VideoCache() if use_cache else None
    
    def get_video_files(
        self,
        path,
        recursive=False,
        folder_id=None,
        force_refresh=False,
    ):
        """Get all video files in a directory
        
        Args:
            path: Directory path to scan
            recursive: If True, scan subdirectories as well
            folder_id: Optional folder ID for caching
            force_refresh: If True, bypass cache and rescan
            
        Returns:
            List of dicts with file information
        """

        t0 = time.perf_counter()

        # If no cache context, fall back to the original behavior.
        if not self.cache or folder_id is None:
            video_files = self._scan_video_files(path, recursive)
            if recursive:
                for video in video_files:
                    if not isinstance(video, dict):
                        continue
                    self._add_series_and_season_fields(video, library_root=path)
            out = [self._sanitize_video_for_api(v) for v in video_files]
            logger.info(
                "VideoManager.get_video_files timing mode=no-cache folder_id=%s recursive=%s force_refresh=%s videos=%s total=%.3fs",
                folder_id,
                bool(recursive),
                bool(force_refresh),
                len(out),
                time.perf_counter() - t0,
            )
            return out

        # Cache-aware incremental processing.
        self.cache.register_folder(folder_id, path, recursive)

        # Backward compatibility: some callers/tests monkeypatch `self.cache` with
        # a minimal stub that only supports the bulk cache APIs.
        required_methods = (
            'get_video_cache_freshness',
            'get_cached_video_by_path',
            'upsert_video',
            'delete_videos_not_in_paths',
            'update_folder_last_scan',
        )
        if not all(hasattr(self.cache, m) for m in required_methods):
            if not force_refresh:
                cached_videos = self.cache.get_cached_videos(folder_id)
                if cached_videos is not None:
                    return cached_videos

            t_scan0 = time.perf_counter()
            video_files = self._scan_video_files(path, recursive)
            t_scan = time.perf_counter() - t_scan0
            if recursive:
                for video in video_files:
                    if not isinstance(video, dict):
                        continue
                    self._add_series_and_season_fields(video, library_root=path)

            t_sanitize0 = time.perf_counter()
            sanitized_videos = [self._sanitize_video_for_api(v) for v in video_files]
            t_sanitize = time.perf_counter() - t_sanitize0

            series_tree = None
            t_tree = None
            if recursive:
                try:
                    t_tree0 = time.perf_counter()
                    series_tree = self._build_series_tree_from_videos(path, sanitized_videos)
                    t_tree = time.perf_counter() - t_tree0
                except Exception:
                    series_tree = None
                    t_tree = None

            try:
                t_cache0 = time.perf_counter()
                self.cache.cache_videos(folder_id, video_files, series_tree=series_tree)
                t_cache = time.perf_counter() - t_cache0
            except Exception as e:
                print(f"Warning: Failed to cache videos for folder {folder_id}: {e}")
                t_cache = None

            logger.info(
                "VideoManager.get_video_files timing mode=cache-stub folder_id=%s recursive=%s force_refresh=%s videos=%s scan=%.3fs sanitize=%.3fs series_tree=%s cache_write=%s total=%.3fs",
                folder_id,
                bool(recursive),
                bool(force_refresh),
                len(sanitized_videos),
                t_scan,
                t_sanitize,
                (f"{t_tree:.3f}s" if isinstance(t_tree, float) else "n/a"),
                (f"{t_cache:.3f}s" if isinstance(t_cache, float) else "n/a"),
                time.perf_counter() - t0,
            )

            return sanitized_videos

        # Fast path: if we already have a valid cached list for this folder and
        # the caller did not explicitly request a refresh, return it immediately
        # without walking the filesystem.
        #
        # This matches the Video Library UX expectation that filesystem changes
        # (new/deleted files, updated NFOs) are only reflected after a refresh.
        if not force_refresh:
            try:
                t_cache_list0 = time.perf_counter()
                cached_videos = self.cache.get_cached_videos(folder_id)
                t_cache_list = time.perf_counter() - t_cache_list0
                if cached_videos is not None:
                    logger.info(
                        "VideoManager.get_video_files timing mode=cache-only folder_id=%s recursive=%s force_refresh=%s videos=%s cache_list=%.3fs total=%.3fs",
                        folder_id,
                        bool(recursive),
                        bool(force_refresh),
                        len(cached_videos) if isinstance(cached_videos, list) else -1,
                        t_cache_list,
                        time.perf_counter() - t0,
                    )
                    return cached_videos
            except Exception:
                pass

        processed_videos: list[dict] = []
        seen_paths: set[str] = set()

        counts: dict[str, int] = defaultdict(int)
        timings: dict[str, float] = defaultdict(float)

        def _latest_source_mtime(video_path: str) -> float:
            file_mtime = 0.0
            nfo_mtime = 0.0
            try:
                file_mtime = os.path.getmtime(video_path)
            except Exception:
                file_mtime = 0.0
            try:
                nfo_path = find_nfo_file(video_path)
                if nfo_path:
                    nfo_mtime = os.path.getmtime(nfo_path)
            except Exception:
                nfo_mtime = 0.0
            return max(float(file_mtime or 0.0), float(nfo_mtime or 0.0))

        def handle_file(full_path: str, file_name: str):
            ext = os.path.splitext(file_name)[1].lower()
            if ext not in self.VIDEO_EXTENSIONS:
                return

            counts['files_supported'] += 1

            normalized_path = os.path.normpath(full_path)
            seen_paths.add(normalized_path)

            # 1) Check DB registration + freshness
            if not force_refresh:
                try:
                    t_fresh0 = time.perf_counter()
                    freshness = self.cache.get_video_cache_freshness(normalized_path)
                    timings['cache_freshness'] += time.perf_counter() - t_fresh0
                    cached_at = freshness.get('cached_at') if isinstance(freshness, dict) else None
                    if isinstance(cached_at, (int, float)):
                        t_mtime0 = time.perf_counter()
                        latest_change = _latest_source_mtime(normalized_path)
                        timings['source_mtime'] += time.perf_counter() - t_mtime0
                        if float(cached_at) >= float(latest_change):
                            t_get0 = time.perf_counter()
                            cached_video = self.cache.get_cached_video_by_path(normalized_path)
                            timings['cache_get_video'] += time.perf_counter() - t_get0
                            if isinstance(cached_video, dict):
                                counts['files_skipped_cache'] += 1
                                processed_videos.append(cached_video)
                                return
                except Exception:
                    counts['cache_check_errors'] += 1
                    pass

            # 2) Not skipped => extract metadata
            try:
                t_stat0 = time.perf_counter()
                stat = os.stat(normalized_path)
                timings['os_stat'] += time.perf_counter() - t_stat0
            except OSError:
                counts['os_stat_errors'] += 1
                return

            video_info = {
                'path': normalized_path,
                'name': file_name,
                'title': os.path.splitext(file_name)[0],
                'size': stat.st_size,
                'modified': stat.st_mtime,
            }

            try:
                t_meta0 = time.perf_counter()
                metadata = read_video_metadata(
                    normalized_path,
                    include_duration=True,
                    check_nfo=True,
                    include_thumbnail=True,
                )
                timings['read_video_metadata'] += time.perf_counter() - t_meta0
                for key, value in metadata.items():
                    if value is not None:
                        video_info[key] = value
            except Exception:
                counts['metadata_errors'] += 1
                pass

            if 'index_number' not in video_info or video_info.get('index_number') is None:
                t_idx0 = time.perf_counter()
                inferred = self._infer_index_number_from_filename(file_name)
                timings['infer_index_number'] += time.perf_counter() - t_idx0
                if inferred is not None:
                    video_info['index_number'] = inferred

            if recursive:
                t_series0 = time.perf_counter()
                self._add_series_and_season_fields(video_info, library_root=path)
                timings['infer_series_season'] += time.perf_counter() - t_series0

            # 3) Write directly into DB (upsert)
            try:
                t_upsert0 = time.perf_counter()
                self.cache.upsert_video(folder_id, video_info)
                timings['cache_upsert_video'] += time.perf_counter() - t_upsert0
            except Exception as e:
                counts['cache_upsert_errors'] += 1
                print(f"Warning: Failed to upsert video {normalized_path}: {e}")

            t_s0 = time.perf_counter()
            processed_videos.append(self._sanitize_video_for_api(video_info))
            timings['sanitize'] += time.perf_counter() - t_s0
            counts['files_processed'] += 1

        try:
            if recursive:
                t_walk0 = time.perf_counter()
                for root, _, files in os.walk(path):
                    for file_name in files:
                        handle_file(os.path.join(root, file_name), file_name)
                timings['os_walk'] += time.perf_counter() - t_walk0
            else:
                t_scan0 = time.perf_counter()
                with os.scandir(path) as entries:
                    for entry in entries:
                        if entry.is_file():
                            handle_file(entry.path, entry.name)
                timings['os_scandir'] += time.perf_counter() - t_scan0
        except Exception as e:
            print(f"Error scanning video directory {path}: {e}")

        # Remove files that no longer exist.
        try:
            t_del0 = time.perf_counter()
            self.cache.delete_videos_not_in_paths(folder_id, seen_paths)
            timings['cache_delete_missing'] += time.perf_counter() - t_del0
        except Exception:
            counts['cache_delete_errors'] += 1
            pass

        # Rebuild cached series/seasons + refresh per-video links.
        if recursive:
            t_series0 = time.perf_counter()
            sanitized_for_series = [self._sanitize_video_for_api(v) for v in processed_videos]
            timings['sanitize_for_series'] += time.perf_counter() - t_series0
            try:
                t_tree0 = time.perf_counter()
                series_tree = self._build_series_tree_from_videos(path, sanitized_for_series)
                timings['build_series_tree'] += time.perf_counter() - t_tree0

                t_cache_tree0 = time.perf_counter()
                self.cache.cache_series_tree(folder_id, series_tree)
                timings['cache_series_tree'] += time.perf_counter() - t_cache_tree0

                t_map0 = time.perf_counter()
                series_id_by_path = self.cache.get_video_series_id_map(folder_id)
                season_id_by_path = self.cache.get_video_season_id_map_for_folder(folder_id)
                timings['cache_series_season_maps'] += time.perf_counter() - t_map0

                t_links0 = time.perf_counter()
                for v in processed_videos:
                    if not isinstance(v, dict):
                        continue
                    vpath = v.get('path')
                    if not isinstance(vpath, str) or not vpath:
                        continue
                    try:
                        rel = os.path.relpath(os.path.normpath(vpath), path)
                        parts = [p for p in rel.split(os.sep) if p and p not in ('.', '..')]
                        series_id = None
                        season_id = None
                        if len(parts) >= 2:
                            series_full_path = os.path.normpath(os.path.join(path, parts[0]))
                            series_id = series_id_by_path.get(series_full_path)
                        if len(parts) >= 3:
                            season_full_path = os.path.normpath(os.path.join(path, parts[0], parts[1]))
                            season_id = season_id_by_path.get(season_full_path)
                        self.cache.update_video_series_season_links(
                            folder_id,
                            vpath,
                            series_id=series_id,
                            season_id=season_id,
                        )
                    except Exception:
                        continue
                timings['cache_update_links'] += time.perf_counter() - t_links0
            except Exception:
                counts['series_tree_errors'] += 1
                pass

        try:
            t_last_scan0 = time.perf_counter()
            self.cache.update_folder_last_scan(folder_id)
            timings['cache_update_folder_last_scan'] += time.perf_counter() - t_last_scan0
        except Exception:
            counts['cache_update_last_scan_errors'] += 1
            pass

        t_sort0 = time.perf_counter()
        processed_videos.sort(key=lambda x: (x.get('title') or x.get('name') or '').lower() if isinstance(x, dict) else '')
        timings['sort'] += time.perf_counter() - t_sort0

        out = [v if isinstance(v, dict) and 'has_thumbnail' in v else self._sanitize_video_for_api(v) for v in processed_videos]

        logger.info(
            "VideoManager.get_video_files timing mode=cache-aware folder_id=%s recursive=%s force_refresh=%s videos=%s supported=%s skipped_cache=%s processed=%s total=%.3fs phase=%s",
            folder_id,
            bool(recursive),
            bool(force_refresh),
            len(out),
            counts.get('files_supported', 0),
            counts.get('files_skipped_cache', 0),
            counts.get('files_processed', 0),
            time.perf_counter() - t0,
            {
                'walk': round(timings.get('os_walk', 0.0), 3),
                'scandir': round(timings.get('os_scandir', 0.0), 3),
                'freshness': round(timings.get('cache_freshness', 0.0), 3),
                'mtime': round(timings.get('source_mtime', 0.0), 3),
                'get_cached': round(timings.get('cache_get_video', 0.0), 3),
                'stat': round(timings.get('os_stat', 0.0), 3),
                'metadata': round(timings.get('read_video_metadata', 0.0), 3),
                'upsert': round(timings.get('cache_upsert_video', 0.0), 3),
                'delete_missing': round(timings.get('cache_delete_missing', 0.0), 3),
                'series_tree': round(timings.get('build_series_tree', 0.0), 3),
                'cache_series_tree': round(timings.get('cache_series_tree', 0.0), 3),
                'cache_maps': round(timings.get('cache_series_season_maps', 0.0), 3),
                'cache_links': round(timings.get('cache_update_links', 0.0), 3),
                'update_last_scan': round(timings.get('cache_update_folder_last_scan', 0.0), 3),
                'sanitize': round(timings.get('sanitize', 0.0), 3),
                'sanitize_for_series': round(timings.get('sanitize_for_series', 0.0), 3),
                'sort': round(timings.get('sort', 0.0), 3),
            },
        )

        return out

    def _build_series_tree_from_videos(self, library_root: str, videos: list[dict]) -> list[dict]:
        """Build a hierarchical Series -> Seasons -> Videos structure.

        This expects videos already enriched with inferred `series` and `season`
        fields and sanitized for API (so that `media_id` and `has_thumbnail` are
        available for cover selection).
        """
        by_series: dict[str, list[dict]] = {}
        for v in videos:
            if not isinstance(v, dict):
                continue
            series_name = v.get('series')
            if not isinstance(series_name, str) or not series_name.strip():
                continue
            by_series.setdefault(series_name, []).append(v)

        series_items: list[Series] = []
        for series_name, series_videos in sorted(by_series.items(), key=lambda kv: kv[0].lower()):
            series_path = os.path.join(library_root, series_name)
            series_public_id = f"ser_{hashlib.sha1(os.path.normpath(series_path).lower().encode('utf-8', errors='ignore')).hexdigest()[:12]}"

            series_nfo = self._read_folder_nfo_metadata(series_path, 'tvshow.nfo')
            series_title = (series_nfo.get('title') or series_name).strip() if isinstance(series_nfo.get('title') or series_name, str) else series_name
            series_tags = series_nfo.get('tags') if isinstance(series_nfo.get('tags'), list) else self._union_tags_from_videos(series_videos)
            series_user_rating = series_nfo.get('user_rating') if isinstance(series_nfo.get('user_rating'), (int, float)) else self._avg_user_rating_from_videos(series_videos)
            series_artists = self._split_artist_string(series_nfo.get('artist')) or self._union_artists_from_videos(series_videos)
            series_cover = self._pick_series_cover(series_public_id, series_path, series_videos)

            series_obj = Series(
                id=series_public_id,
                full_path=series_path,
                title=series_title,
                user_rating=series_user_rating,
                tags=series_tags,
                artists=series_artists,
                cover=series_cover,
            )

            season_buckets: dict[str, list[dict]] = {}
            series_root_videos: list[dict] = []
            for v in series_videos:
                season_name = v.get('season')
                if isinstance(season_name, str) and season_name.strip():
                    season_buckets.setdefault(season_name, []).append(v)
                else:
                    series_root_videos.append(v)

            def _video_sort_key(video: dict):
                idx = video.get('index_number')
                if isinstance(idx, int):
                    return (0, idx, (video.get('title') or '').lower(), (video.get('path') or ''))
                return (1, (video.get('title') or '').lower(), (video.get('path') or ''))

            series_obj.videos = sorted(series_root_videos, key=_video_sort_key)

            seasons: list[Season] = []
            for season_name, season_videos in sorted(season_buckets.items(), key=lambda kv: kv[0].lower()):
                season_path = os.path.join(series_path, season_name)
                season_public_id = f"sea_{hashlib.sha1(os.path.normpath(season_path).lower().encode('utf-8', errors='ignore')).hexdigest()[:12]}"
                season_index = self._infer_season_index_from_folder_name(season_name)

                season_nfo = self._read_folder_nfo_metadata(season_path, 'season.nfo')
                season_title = season_nfo.get('title') if isinstance(season_nfo.get('title'), str) else None
                if not season_title:
                    season_title = f"Season {season_index}" if isinstance(season_index, int) else season_name

                season_tags = season_nfo.get('tags') if isinstance(season_nfo.get('tags'), list) else self._union_tags_from_videos(season_videos)
                season_user_rating = season_nfo.get('user_rating') if isinstance(season_nfo.get('user_rating'), (int, float)) else self._avg_user_rating_from_videos(season_videos)
                season_artists = self._split_artist_string(season_nfo.get('artist')) or self._union_artists_from_videos(season_videos)

                season_cover = self._pick_season_cover(season_public_id, series_path, season_index, season_videos)

                seasons.append(
                    Season(
                        id=season_public_id,
                        full_path=season_path,
                        title=season_title,
                        user_rating=season_user_rating,
                        tags=season_tags,
                        artists=season_artists,
                        cover=season_cover,
                        index_number=season_index,
                        videos=sorted(season_videos, key=_video_sort_key),
                    )
                )

            series_obj.seasons = seasons
            series_items.append(series_obj)

        return [s.to_dict() for s in series_items]

    @staticmethod
    def _find_first_existing(paths: list[str]) -> str | None:
        for p in paths:
            try:
                if p and os.path.exists(p):
                    return p
            except Exception:
                continue
        return None

    def _find_series_poster_file(self, series_path: str) -> str | None:
        if not isinstance(series_path, str) or not series_path:
            return None
        candidates = [
            os.path.join(series_path, 'poster.jpg'),
            os.path.join(series_path, 'poster.jpeg'),
            os.path.join(series_path, 'poster.png'),
            os.path.join(series_path, 'poster.webp'),
        ]
        return self._find_first_existing(candidates)

    def _find_season_poster_file(self, series_path: str, season_index: int | None) -> str | None:
        if not isinstance(series_path, str) or not series_path:
            return None
        if not isinstance(season_index, int):
            return None

        # As per spec: poster stored in the series folder, named like season01-poster.jpg.
        base_names = [
            f'season{season_index:02d}-poster',
            f'season{season_index}-poster',
        ]
        exts = ['.jpg', '.jpeg', '.png', '.webp']
        candidates: list[str] = []
        for bn in base_names:
            for ext in exts:
                candidates.append(os.path.join(series_path, f'{bn}{ext}'))
        return self._find_first_existing(candidates)

    def _pick_series_cover(self, series_public_id: str, series_path: str, videos: list[dict]) -> str | None:
        poster = self._find_series_poster_file(series_path)
        if poster and getattr(self, 'cache', None) is not None and getattr(self.cache, 'db', None) is not None:
            try:
                if self.cache.db.ensure_video_artwork_from_source(series_public_id, poster):
                    return f"/api/video/thumbnail/by-art-id/{series_public_id}"
            except Exception:
                pass
        return self._pick_cover_from_videos(videos)

    def _pick_season_cover(self, season_public_id: str, series_path: str, season_index: int | None, videos: list[dict]) -> str | None:
        poster = self._find_season_poster_file(series_path, season_index)
        if poster and getattr(self, 'cache', None) is not None and getattr(self.cache, 'db', None) is not None:
            try:
                if self.cache.db.ensure_video_artwork_from_source(season_public_id, poster):
                    return f"/api/video/thumbnail/by-art-id/{season_public_id}"
            except Exception:
                pass
        return self._pick_cover_from_videos(videos)

    @staticmethod
    def _add_series_and_season_fields(video: dict, *, library_root: str) -> None:
        """Infer series + season from a video's path relative to the library root.

        - Series: top-level folder inside the library root
        - Season: second-level folder inside a series folder
        """
        video_path = video.get('path')
        if not isinstance(video_path, str) or not video_path:
            return

        try:
            rel = os.path.relpath(video_path, library_root)
        except Exception:
            return

        parts = [p for p in rel.split(os.sep) if p and p not in ('.', '..')]
        if len(parts) >= 2:
            video.setdefault('series', parts[0])
        if len(parts) >= 3:
            video.setdefault('season', parts[1])

    @staticmethod
    def _infer_index_number_from_filename(file_name: str) -> int | None:
        """Best-effort episode/index extraction from common filename patterns."""
        if not file_name:
            return None
        base = os.path.splitext(os.path.basename(file_name))[0]

        patterns = [
            # S01E02 / s1e2
            re.compile(r'(?i)\bs\d{1,2}\s*e(\d{1,3})\b'),
            # 1x02
            re.compile(r'(?i)\b\d{1,2}x(\d{1,3})\b'),
            # "02 - Title" / "02. Title" / "02_Title"
            re.compile(r'^\s*(\d{1,3})\s*[\-._ ]\s*'),
        ]

        for pat in patterns:
            m = pat.search(base)
            if not m:
                continue
            try:
                value = int(m.group(1))
            except Exception:
                continue
            if value >= 0:
                return value
        return None

    @staticmethod
    def _sanitize_video_for_api(video: dict) -> dict:
        """Return a JSON-safe video dict.

        - Never include raw thumbnail bytes in API responses.
        - Provide `has_thumbnail` boolean for UI.
        - Preserve `thumbnail_url` (from NFO) if present.
        """
        sanitized = dict(video)

        # Provide stable cache identifier even when returning fresh scan results.
        video_path = sanitized.get('path')
        if isinstance(video_path, str) and video_path:
            normalized_path = os.path.normpath(video_path)
            sanitized['media_id'] = hashlib.sha256(normalized_path.encode('utf-8', errors='replace')).hexdigest()

        # If cache already provided `has_thumbnail`, trust it.
        has_thumbnail = sanitized.get('has_thumbnail')

        thumbnail_value = sanitized.pop('thumbnail', None)
        sanitized.pop('thumbnail_mime_type', None)

        if isinstance(thumbnail_value, (bytes, bytearray, memoryview)):
            has_thumbnail = True
        elif isinstance(thumbnail_value, str):
            # Backward compatibility: older metadata used `thumbnail` for NFO URL.
            sanitized.setdefault('thumbnail_url', thumbnail_value)

        if has_thumbnail is None:
            has_thumbnail = False

        sanitized['has_thumbnail'] = bool(has_thumbnail)
        return sanitized
    
    def _scan_video_files(self, path, recursive=False):
        """Scan filesystem for video files
        
        Args:
            path: Directory path to scan
            recursive: If True, scan subdirectories as well
            
        Returns:
            List of dicts with file information
        """
        t0 = time.perf_counter()
        video_files = []

        counts: dict[str, int] = defaultdict(int)
        timings: dict[str, float] = defaultdict(float)
        
        try:
            if not os.path.exists(path):
                return video_files

            def handle_file(full_path: str, file_name: str):
                ext = os.path.splitext(file_name)[1].lower()
                if ext not in self.VIDEO_EXTENSIONS:
                    return

                counts['files_supported'] += 1

                try:
                    t_stat0 = time.perf_counter()
                    stat = os.stat(full_path)
                    timings['os_stat'] += time.perf_counter() - t_stat0
                except OSError:
                    counts['os_stat_errors'] += 1
                    return

                # Create track info with basic file metadata
                video_info = {
                    'path': full_path,
                    'name': file_name,
                    'title': os.path.splitext(file_name)[0],
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                }
                
                # Extract metadata from video file and NFO file
                try:
                    t_meta0 = time.perf_counter()
                    metadata = read_video_metadata(
                        full_path,
                        include_duration=True,
                        check_nfo=True,
                        include_thumbnail=True
                    )
                    timings['read_video_metadata'] += time.perf_counter() - t_meta0
                    # Merge metadata, keeping existing values if not in metadata
                    for key, value in metadata.items():
                        if value is not None:
                            video_info[key] = value
                except Exception as e:
                    # If metadata extraction fails, continue with basic info
                    counts['metadata_errors'] += 1
                    pass

                # Best-effort index number extraction (episodes, parts, etc).
                if 'index_number' not in video_info or video_info.get('index_number') is None:
                    t_idx0 = time.perf_counter()
                    inferred = self._infer_index_number_from_filename(file_name)
                    timings['infer_index_number'] += time.perf_counter() - t_idx0
                    if inferred is not None:
                        video_info['index_number'] = inferred
                
                video_files.append(video_info)
                counts['files_added'] += 1

            if recursive:
                t_walk0 = time.perf_counter()
                for root, dirs, files in os.walk(path):
                    for file_name in files:
                        full_path = os.path.join(root, file_name)
                        handle_file(full_path, file_name)
                timings['os_walk'] += time.perf_counter() - t_walk0
            else:
                t_scan0 = time.perf_counter()
                with os.scandir(path) as entries:
                    for entry in entries:
                        if entry.is_file():
                            handle_file(entry.path, entry.name)
                timings['os_scandir'] += time.perf_counter() - t_scan0
                            
        except Exception as e:
            print(f"Error scanning video directory {path}: {e}")
        
        # Sort by name
        t_sort0 = time.perf_counter()
        video_files.sort(key=lambda x: x['name'].lower())
        timings['sort'] += time.perf_counter() - t_sort0

        logger.info(
            "VideoManager._scan_video_files timing recursive=%s path=%s supported=%s added=%s walk=%.3fs scandir=%.3fs stat=%.3fs metadata=%.3fs sort=%.3fs total=%.3fs",
            bool(recursive),
            path,
            counts.get('files_supported', 0),
            counts.get('files_added', 0),
            timings.get('os_walk', 0.0),
            timings.get('os_scandir', 0.0),
            timings.get('os_stat', 0.0),
            timings.get('read_video_metadata', 0.0),
            timings.get('sort', 0.0),
            time.perf_counter() - t0,
        )
        return video_files

    @staticmethod
    def _split_artist_string(artist: str | None) -> list[str]:
        if not artist:
            return []
        parts = [p.strip() for p in artist.split(',')]
        return [p for p in parts if p]

    @staticmethod
    def _pick_cover_from_videos(videos: list[dict]) -> str | None:
        """Pick a cover URL for a series/season based on its videos.

        Prefers the cached thumbnail endpoint when a `media_id` thumbnail exists,
        otherwise falls back to `thumbnail_url` when present.
        """
        for v in videos:
            if not isinstance(v, dict):
                continue
            media_id = v.get('media_id')
            has_thumb = v.get('has_thumbnail')
            if isinstance(media_id, str) and media_id and bool(has_thumb):
                return f"/api/video/thumbnail/by-id/{media_id}"
        for v in videos:
            if not isinstance(v, dict):
                continue
            thumb_url = v.get('thumbnail_url')
            if isinstance(thumb_url, str) and thumb_url.strip():
                return thumb_url.strip()
        return None

    @staticmethod
    def _union_tags_from_videos(videos: list[dict]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for v in videos:
            tags = v.get('tags') if isinstance(v, dict) else None
            if not isinstance(tags, list):
                continue
            for t in tags:
                if not isinstance(t, str):
                    continue
                tt = t.strip()
                if not tt or tt in seen:
                    continue
                seen.add(tt)
                out.append(tt)
        return out

    def _union_artists_from_videos(self, videos: list[dict]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for v in videos:
            artist_str = v.get('artist') if isinstance(v, dict) else None
            for a in self._split_artist_string(artist_str):
                if a in seen:
                    continue
                seen.add(a)
                out.append(a)
        return out

    @staticmethod
    def _avg_user_rating_from_videos(videos: list[dict]) -> float | None:
        values: list[float] = []
        for v in videos:
            r = v.get('user_rating') if isinstance(v, dict) else None
            if isinstance(r, (int, float)):
                values.append(float(r))
        if not values:
            return None
        return sum(values) / len(values)

    @staticmethod
    def _infer_season_index_from_folder_name(folder_name: str) -> int | None:
        if not folder_name:
            return None
        name = folder_name.strip()

        # S01 / s1
        m = re.search(r'(?i)\bs\s*(\d{1,3})\b', name)
        if m:
            try:
                return int(m.group(1))
            except Exception:
                return None

        # Season 01
        m = re.search(r'(?i)\bseason\s*(\d{1,3})\b', name)
        if m:
            try:
                return int(m.group(1))
            except Exception:
                return None

        # Plain numeric
        if name.isdigit():
            try:
                return int(name)
            except Exception:
                return None
        return None

    def _read_folder_nfo_metadata(self, folder_path: str, nfo_name: str) -> dict:
        """Read metadata from a folder-level NFO file if present.

        Uses the existing NFO parser used for videos; fields are then reshaped for
        Series/Season schema.
        """
        try:
            nfo_path = os.path.join(folder_path, nfo_name)
            if not os.path.exists(nfo_path):
                return {}
            # Reuse the existing parser behavior by reading as NFO directly.
            # We don't want thumbnails from a folder; just parsed fields.
            from services.video.video_metadata import parse_nfo_file

            return parse_nfo_file(nfo_path)
        except Exception:
            return {}

    def build_series_tree(
        self,
        library_root: str,
        *,
        folder_id: int | None = None,
        force_refresh: bool = False,
    ) -> list[dict]:
        """Build a hierarchical Series -> Seasons -> Videos structure.

        This is intended for recursive libraries. Series and Season are inferred
        from folder structure.
        """
        videos = self.get_video_files(
            library_root,
            recursive=True,
            folder_id=folder_id,
            force_refresh=force_refresh,
        )

        return self._build_series_tree_from_videos(library_root, videos)
    
    def create_playlist(self, playlist_path, videos, base_path=None):
        """Create an M3U playlist file from a list of videos
        
        Args:
            playlist_path: Full path where the playlist file will be created
            videos: List of video dicts with 'path' key
            base_path: Optional base path to make video paths relative to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            playlist_dir = os.path.dirname(playlist_path)
            
            with open(playlist_path, 'w', encoding='utf-8') as f:
                f.write('#EXTM3U\n')
                
                for video in videos:
                    video_path = video.get('path', '')
                    if not video_path:
                        continue
                    
                    # Make path relative to playlist directory if possible
                    if base_path and os.path.isabs(video_path):
                        try:
                            video_path = os.path.relpath(video_path, playlist_dir)
                        except ValueError:
                            # Can't make relative (different drives on Windows)
                            pass
                    
                    # Write extended info
                    title = video.get('title', os.path.basename(video_path))
                    f.write(f'#EXTINF:-1,{title}\n')
                    f.write(f'{video_path}\n')
            
            return True
        except Exception as e:
            print(f"Error creating playlist {playlist_path}: {e}")
            return False
    
    def search_videos(self, videos, title=None):
        """Filter videos by search criteria
        
        Args:
            videos: List of video dicts
            title: Filter by title (case-insensitive substring match)
            
        Returns:
            Filtered list of videos
        """
        filtered = videos
        
        if title:
            title_lower = title.lower()
            filtered = [
                v for v in filtered 
                if title_lower in v.get('title', '').lower() or 
                   title_lower in v.get('name', '').lower()
            ]
        
        return filtered
    
    def invalidate_cache(self, folder_id):
        """Invalidate cache for a specific folder"""
        if self.cache:
            self.cache.invalidate_folder(folder_id)
    
    def clear_cache(self):
        """Clear all cached data"""
        if self.cache:
            self.cache.clear_cache()
    
    def get_cache_stats(self):
        """Get cache statistics"""
        if self.cache:
            return self.cache.get_cache_stats()
        return {'folders': 0, 'videos': 0, 'total_size_bytes': 0}

