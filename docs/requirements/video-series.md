# Video Series View Requirements (`/video/series`)

## Purpose

The Video Series view provides a series-first browsing experience for videos in a selected configured Video Library.

A **Series** is inferred from folder structure when the library is configured as recursive:
- **Series**: top-level folder inside the video library folder.
- **Season**: next-level folder inside a series folder.

## Video Library selection

- The page shows one button per configured video library folder (from `GET /api/video/libraries`).
- The user can select a library.
- A star icon allows setting a default library for future visits.
  - Stored in browser `localStorage` under `videoSeries.defaultLibraryId`.

URL behavior:
- The selected video library is reflected in the URL as `libraryId=<video_library.id>`.

## Series listing

- For the selected library, series are loaded from:
  - `GET /api/video/libraries/<id>/series`
- If the selected library is not recursive, the API returns an empty list and the UI shows:
  - “No series found in this library.”
  - A hint that series require recursive scanning.
- The page shows all returned series as cover tiles (similar visual style to Video Explorer tiles).
  - If a series has a cover URL, it is displayed.
  - Otherwise a placeholder icon is shown.

### Series/Season thumbnails

- A Series may have a poster image in its folder:
  - `SERIES/poster.jpg`
- A Season may have a poster image stored in the Series folder (not inside the season folder):
  - For Season 1 (`SERIES/S01/`), the poster may be `SERIES/season01-poster.jpg`
- When these poster files exist, the backend caches them using the same thumbnail storage mechanism as video thumbnails and serves them via:
  - `GET /api/video/thumbnail/by-art-id/<series_or_season_id>`
- The `cover` field in the series tree response points at that API route when a cached poster is available.

## Series details (URL-addressable popup)

- Clicking a series tile opens a modal-style popup.
- The opened series is reflected in the URL via query parameters:
  - `seriesId=<series.id>`
  - Optionally `seasonId=<season.id>` when a season is selected.

Backward compatibility:
- Existing deep-links using `series=<series.full_path>` and `season=<season.full_path>` should still open the correct series/season.

## Seasons and episodes

- If the selected series includes seasons:
  - The popup displays a list of season buttons.
  - Selecting a season shows the season’s episode/video list.
- If the series has no seasons:
  - The popup shows the series’ `videos` list.

Episode/video ordering in the popup:
- If any items in the shown list have `index_number`, the list is sorted by `index_number` ascending.
- If no items have `index_number`, the list is sorted by `premiere_date` ascending (oldest first).
- When values are missing or ties occur, the UI uses a stable fallback (title/path) to keep ordering deterministic.

## Playback

- Each episode/video row has a `Play` button.
- Clicking `Play` calls:
  - `POST /api/video/playback/play-video` with `{ "media_id": "..." }`
- Errors are shown in the page error banner.
