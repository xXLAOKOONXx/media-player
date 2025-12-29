# Video Series View Requirements (`/video/series`)

## Purpose

The Video Series view provides a series-first browsing experience for videos in a selected configured Video Library.

A **Series** is inferred from folder structure when the library is configured as recursive:
- **Series**: top-level folder inside the video library folder.
- **Season**: next-level folder inside a series folder.

## Video Library selection

- The top of the page shows a compact library selector (from `GET /api/video/libraries`).
- The selector can be collapsed/expanded:
  - When collapsed, it shows the currently selected library name and an expand toggle.
  - When expanded, it shows one button per configured video library folder.
- The selector is collapsed by default.
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
- The page groups Series into horizontal carousel rows, similar to the Video Explorer tag rows.
- Each Series is shown as a cover tile.
  - If a Series has a cover URL, it is displayed.
  - Otherwise a placeholder icon is shown.

### Carousel rows

- The top row is **Recently Watched**.
  - It shows up to 10 Series, sorted by the most recent `last_played` timestamp found among any episodes/videos in that Series.
  - Only Series with at least one `last_played` are included.
- Below that, one carousel row is shown per Series tag.
  - A Series appears in every row for each tag it has.
  - Tag rows match the carousel interaction pattern from Video Explorer (arrow buttons when the row is scrollable).
  - Within a tag row, Series are sorted by a recommendation score (highest first), following the same concept as the Video Explorer rows:
    - The UI derives a Series score from its episodes/videos (using their `promotion_score`).
    - Ties are broken deterministically (title/path).

### Series tile watch status

- If a Series has some watched episodes/videos (`playcount > 0` for at least one item, but not all items), the Series tile shows a **Play** icon badge to indicate “Started watching”.
- If all episodes/videos in a Series are watched (`playcount > 0` for every item), the Series tile shows an **Eye** icon badge to indicate “Fully watched”.

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

Season watch status:
- If all episodes in a Season are watched (`playcount > 0` for every episode), that Season button is highlighted with a grayish-green background.
- If the series has no seasons:
  - The popup shows the series’ `videos` list.

Episode/video ordering in the popup:
- If any items in the shown list have `index_number`, the list is sorted by `index_number` ascending.
- If no items have `index_number`, the list is sorted by `premiere_date` ascending (oldest first).
- When values are missing or ties occur, the UI uses a stable fallback (title/path) to keep ordering deterministic.

### Episodes display (carousel)

- The episode list is displayed as a horizontal carousel row, matching the layout used in the Video Explorer tag rows.
- Each episode is shown as a thumbnail tile.
- If an episode has been watched (`playcount > 0`), it shows the same “Watched” marker as the Video Explorer tiles.

Tile behavior:
- Clicking an episode tile starts playback immediately via `POST /api/video/playback/play-video`.

## Playback

- Each episode/video row has a `Play` button.
- Clicking `Play` calls:
  - `POST /api/video/playback/play-video` with `{ "media_id": "..." }`
- Errors are shown in the page error banner.

## Episode actions

Below the episode carousel, the popup provides three buttons:

- **Continue watching**
  - Finds the most recently watched video across the entire selected Series (based on `last_played`).
  - Determines the “next” episode in that same season/group and adds it, plus every remaining episode until the end of that season, to the current watching queue.
  - Adds the selected set using `POST /api/video/playback/add-videos` with `{ "media_ids": ["..."] }`.

- **Play Random**
  - Adds one random episode from the currently displayed episode list (current season if selected, otherwise the series-level videos list) to the current watching queue.
  - Uses `POST /api/video/playback/add-videos`.

- **Play Random Unseen**
  - Adds one random episode from the currently displayed episode list where `playcount == 0`.
  - Uses `POST /api/video/playback/add-videos`.
