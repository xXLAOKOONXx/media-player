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

## Series listing

- For the selected library, series are loaded from:
  - `GET /api/video/libraries/<id>/series`
- If the selected library is not recursive, the API returns an empty list and the UI shows:
  - “No series found in this library.”
  - A hint that series require recursive scanning.
- The page shows all returned series as cover tiles (similar visual style to Video Explorer tiles).
  - If a series has a cover URL, it is displayed.
  - Otherwise a placeholder icon is shown.

## Series details (URL-addressable popup)

- Clicking a series tile opens a modal-style popup.
- The opened series is reflected in the URL via query parameters:
  - `series=<series.full_path>`
  - Optionally `season=<season.full_path>` when a season is selected.

## Seasons and episodes

- If the selected series includes seasons:
  - The popup displays a list of season buttons.
  - Selecting a season shows the season’s episode/video list.
- If the series has no seasons:
  - The popup shows the series’ `videos` list.

## Playback

- Each episode/video row has a `Play` button.
- Clicking `Play` calls:
  - `POST /api/video/playback/play-video` with `{ "media_id": "..." }`
- Errors are shown in the page error banner.
