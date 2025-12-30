# Video Explorer (`/video/explorer`)

## Purpose

The Video Explorer page provides a browsing experience for videos inside a selected configured Video Library folder.

- The explorer view uses the full available page width.

## Video Library selection

- The top of the page shows a compact library selector (from `GET /api/video/libraries`).
- The selector can be collapsed/expanded:
  - When collapsed, it shows the currently selected library name and an expand toggle.
  - When expanded, it shows one button per configured video library folder.
- The selector is collapsed by default.
- Each folder button displays the user-assigned folder name.
- On the right side of each folder button there is a star icon:
  - Empty star (`star_border`) indicates the folder is not the default.
  - Filled star (`star`) indicates the folder is the default.
  - Clicking the star sets that folder as the default selection for future visits.
    - This is stored in browser `localStorage` under `videoExplorer.defaultLibraryId`.
- The library selector header also shows a star icon for the currently selected library (same default behavior).
- Clicking a folder button selects it and loads its videos.

## Browse view (Netflix-style)

- Below the folder selection, a browsing section appears.
- The selected library’s videos are loaded from `GET /api/video/libraries/<id>/videos`.
- Each returned video object also includes fields: `playcount`, `last_played` (may be `null` when never played), and `promotion_score`.
- A "Daily Suggestions" carousel is shown above the tag rows:
  - It includes the top 50 videos in the selected library by `promotion_score`.
- Each available tag in the selected library creates a carousel:
  - Tags are taken from each video’s `tags` array.
  - Carousels are ordered randomly by tag name (the order is randomized when the library loads).
  - Each carousel shows video thumbnails.
    - Videos within each carousel are sorted by `promotion_score` (highest to lowest).
    - The carousel row height is increased (taller tiles) for easier browsing (50% taller).
    - Each tile sizes to the cover aspect ratio so the full cover is visible without cropping.
    - Video titles are not shown by default on the thumbnails.
    - If the current logged-in user has watched a video (i.e., `playcount > 0`), the thumbnail tile shows a green eye (`visibility`) indicator overlay.
  - The carousel does not show a horizontal scrollbar.
  - Navigation through the carousel is done via left/right arrow buttons positioned on the left and right border of the row.
    - The arrow buttons overlay the covers, span the full row height, and are partially transparent.
    - The arrow buttons use a gradient that fades from the border side toward the inside of the row.
    - If a row is fully scrolled to the left, the left arrow is hidden.
    - If a row is fully scrolled to the right, the right arrow is hidden.
- If no tagged videos exist, the page shows: “No tagged videos found in this library.”

## Video details popup

- Clicking a video thumbnail opens a modal popup with:
  - Title
  - Cover image (thumbnail/poster) when available
  - Description (if available)
  - Editable `Rating` field (user rating) in range 0–10
  - Editable tags list (add/remove)
  - Basic metadata (artist/director, series, duration when available)
  - Editable `music_start` and `music_end` fields (milliseconds) when available
    - Each field shows a tooltip indicating the value is in milliseconds (ms)
  - A `Save` button (persists rating + tags)
  - A `Play` button
- Pressing `Esc` or clicking outside the popup closes it.
- When the popup content is taller than the viewport, the popup scrolls internally and the background page does not scroll.

### Saving rating and tags

- Clicking `Save` calls `POST /api/video/metadata/user` with:
  - `media_id`
  - `user_rating` (number 0–10, or `null` to clear)
  - `tags` (array of strings)
-  - `start_time_in_ms` and `end_time_in_ms` (integer milliseconds, or `null` to clear)
- The save requires authentication.
- Persisting prefers writing to the video’s `.nfo` file when present; otherwise it falls back to embedded MP4 tags (MP4/M4V only).
- On successful save, the popup and browse view reflect the updated rating and tags immediately.

## Playback

- Clicking `Play` starts the selected video immediately by calling:
  - `POST /api/video/playback/play-video` with `{ "media_id": "..." }`
- On success the popup remains open (user can close it manually).

## Thumbnails

- If a video has a cached thumbnail and `media_id`, the UI requests it from:
  - `GET /api/video/thumbnail/by-id/<media_id>`
- If no thumbnail is available, the thumbnail tile falls back to showing the title text.
- If no thumbnail is available (or the thumbnail fails to load), the thumbnail tile falls back to a placeholder icon.
