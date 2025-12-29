# Video Explorer (`/video/explorer`)

## Purpose

The Video Explorer page provides a browsing experience for videos inside a selected configured Video Library folder.

## Video Library selection

- The page shows one button per configured video library folder (from `GET /api/video/libraries`).
- Each folder button displays the user-assigned folder name.
- On the right side of each folder button there is a star icon:
  - Empty star (`star_border`) indicates the folder is not the default.
  - Filled star (`star`) indicates the folder is the default.
  - Clicking the star sets that folder as the default selection for future visits.
    - This is stored in browser `localStorage` under `videoExplorer.defaultLibraryId`.
- Clicking a folder button selects it and loads its videos.

## Browse view (Netflix-style)

- Below the folder selection, a browsing section appears.
- The selected library’s videos are loaded from `GET /api/video/libraries/<id>/videos`.
- Each available tag in the selected library creates a carousel:
  - Tags are taken from each video’s `tags` array.
  - Carousels are ordered alphabetically by tag name.
  - Each carousel shows video thumbnails.
    - The carousel row height is increased (taller tiles) for easier browsing (50% taller).
    - Each tile sizes to the cover aspect ratio so the full cover is visible without cropping.
    - Video titles are not shown by default on the thumbnails.
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
  - Tags (if present)
  - Basic metadata (artist/director, series, duration when available)
  - A `Play` button
- Pressing `Esc` or clicking outside the popup closes it.
- When the popup content is taller than the viewport, the popup scrolls internally and the background page does not scroll.

## Playback

- Clicking `Play` starts the selected video immediately by calling:
  - `POST /api/video/playback/play-video` with `{ "video_path": "..." }`
- On success the popup closes.

## Thumbnails

- If a video has a cached thumbnail and `media_id`, the UI requests it from:
  - `GET /api/video/thumbnail/by-id/<media_id>`
- If no thumbnail is available, the thumbnail tile falls back to showing the title text.
- If no thumbnail is available (or the thumbnail fails to load), the thumbnail tile falls back to a placeholder icon.
