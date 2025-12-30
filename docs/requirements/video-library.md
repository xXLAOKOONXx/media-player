# Video Library View Requirements

URL: `/video/library`

Source component:

- `frontend/src/components/VideoLibrary.tsx`

## Purpose

Manages video library folders, loads videos (single-folder or all folders), filters/searches videos, selects videos in bulk, and creates/updates playlists from selected videos.

## Top header actions

Buttons in the "Video Library" header:

1. **Configure Playlist Folder**: Opens a modal to set the folder used for playlist creation and for listing `.m3u` playlists. Visible to **admin** users only.

1. **Add Video Library**: Opens a modal to add a new video library folder to scan. Visible to **admin** users only.

1. **Search All Folders**: Switches the view into global search mode. Sets `globalSearch = true`, clears `selectedFolder`, and triggers loading videos from all folders.

Conditional buttons (only when at least one video is selected):

1. **Create Playlist (N)**: Opens the "Create New Playlist" modal. Visible to any **logged-in** user.

1. **Add to Current Playlist (N)**: Sends selected videos to the currently loaded playback playlist.

1. **Add to Playlist (N)**: Opens the "Add Selected Videos to Playlist" modal. Visible to any **logged-in** user.

## Playlist Folder indicator

When `playlistFolder` is set (non-empty):

- Display a line "Playlist Folder: {playlistFolder}".

## Loading behavior

### Initial loads

On mount:

- GET `/api/video/libraries` to load video libraries.
- GET `/api/video/playlists-folder` to load the configured playlist folder.

When `playlistFolder` changes and is non-empty:

- GET `/api/video/playlists-folder/files` to load the list of available playlists in the configured folder.
  - Notes:
    - This endpoint is **not** a generic filesystem browser.
    - Requires the user to be authenticated.

### Video loading modes

- If a folder is selected: load videos for that folder:
  - GET `/api/video/libraries/{libraryId}/videos`
- Else if global search is enabled: load videos from all folders:
  - For each folder in `videoLibraries`, GET `/api/video/libraries/{libraryId}/videos` concurrently.

Backend caching behavior:

- `GET /api/video/libraries/{libraryId}/videos` returns the cached video list from the app database when available.
- The backend does not rescan the filesystem on normal loads.
- Filesystem changes (new/deleted files, updated `.nfo` metadata) become visible after the user triggers **Refresh** for that library.

During loading:

- Show a loading spinner and the text "Loading videos...".

### Video object fields

The video objects returned by `GET /api/video/libraries/{libraryId}/videos` include playback statistics fields sourced from the `media-player-stats.db` database:

- `playcount`: number of plays recorded for this video path
- `last_played`: latest play timestamp (Unix epoch seconds) or `null` if never played

## Configure Playlist Folder modal

Opens via **Configure Playlist Folder**.

Controls:

- Text input for folder path (required).
- **Browse** (type=button)
  - POST `/api/browse` with `{ path: <current input or '/'> }`.
  - Shows directory list for navigation.
- Browse results list:
  - Includes a `..` item that browses to `{browsePath}/..`.
  - Lists directories; clicking a directory browses into it.
- **Select Current Folder**
  - Sets the playlist folder path to the current browse path.
  - Clears browse results.
- **Save** (submit)
  - PUT `/api/video/playlists-folder` with `{ path: playlistFolder }`.
  - On success:
    - Close modal.
    - Reload available playlists.
    - `alert('Playlist folder configured successfully!')`.
  - On failure: `alert('Failed to set playlist folder')`.
- **Cancel**
  - Closes modal.
  - Clears browse results.

## Add Video Library modal

Opens via **Add Video Library**.

Fields:

- Library Name (required)
- Folder Path (required)
- Checkbox: "Scan subfolders recursively"

Buttons:

- **Browse**
  - POST `/api/browse` with `{ path: <current input or '/'> }`.
  - Shows directories.
- Browse list includes `..` and directories.
- **Select Current Folder** sets the Folder Path to the current browse path.
- **Add Library** (submit)
  - POST `/api/video/libraries` with `{ name, path, recursive }`.
  - On success: reset form, close modal, reload library list.
- **Cancel** closes modal and clears browse results.

## Create New Playlist modal

Opens via **Create Playlist (N)**.

Behavior:

- If no videos are selected, block action with `alert('Please select at least one video')`.
- If `playlistFolder` is not set, block action with `alert('Please configure a playlist folder first')`.

Fields:

- Playlist Name (required)

Buttons:

- **Create Playlist** (submit)
  - POST `/api/video/playlists/create` with:
    - `playlist_name: newPlaylistName`
    - `media_ids: <selected video media ids>` (derived from the currently filtered list)
  - On success:
    - `alert('Playlist created successfully!')`
    - Close modal
    - Clear selection
    - Reload available playlists
  - On failure: `alert('Failed to create playlist: <server error>')`
  - Requires the user to be authenticated.
- **Cancel** closes the modal.

## Add Video to Playlist modal

Opens via per-video "Add to playlist" action (see Video table).

Controls:

- Playlist select dropdown (required):
  - Default option: "-- Select Playlist --"
  - Options come from `.m3u` files in `playlistFolder`.

Buttons:

- **Add to Playlist** (submit)
  - POST `/api/video/playlists/{selectedPlaylist}/add-video` with `{ media_id: <selected video media id> }`.
  - On success:
    - `alert('Video added to playlist successfully!')`
    - Close modal and clear selection state.
  - On failure: `alert('Failed to add video: <server error>')`
  - Requires the user to be authenticated.
- **Cancel** closes modal and clears modal state.

## Add Selected Videos to Playlist modal

Opens via **Add to Playlist (N)** (top header action).

Controls:

- Playlist select dropdown (required):
  - Default option: "-- Select Playlist --"
  - Options come from `.m3u` files in `playlistFolder`.
- Shows text "{N} video(s) selected".

Buttons:

- **Add to Playlist** (submit)
  - For each selected video (in current table order), POST `/api/video/playlists/{selectedPlaylist}/add-video` with `{ media_id: <selected video media id> }`.
  - On success:
    - `alert('Videos added to playlist successfully!')`
    - Close modal, clear selection.
  - On failure:
    - `alert('Failed to add one or more videos: <server error>')`
  - Requires the user to be authenticated.
- **Cancel** closes modal and clears modal state.

## Video Libraries section

### Collapsing

- "Video Libraries" header is clickable.
- Clicking toggles collapsed state.
- Icon switches between `expand_more` (collapsed) and `expand_less` (expanded).

### Library row selection

- Clicking the library info area:
  - Sets `selectedFolder = library.id`
  - Sets `globalSearch = false`
  - Triggers loading videos for that library.

### Library actions

Per library, when not editing:

- **Refresh** (icon `refresh`, tooltip "Refresh library")
  - POST `/api/video/libraries/{libraryId}/refresh`
  - Reloads videos for the selected library or all libraries if in global search.
- **Edit** (icon `edit`)
  - Enters inline edit mode and pre-fills name.
- **Delete** (icon `delete`)
  - Confirms: "Are you sure you want to delete this video library?"
  - DELETE `/api/video/libraries/{libraryId}`
  - If deleted library was selected: clear selection and videos.

Inline edit mode:

- Text input for library name.
- **Save** (icon `check`)
  - PUT `/api/video/libraries/{libraryId}` with `{ name: editName }`.
  - Exits edit mode and reloads library list.
  - Pressing Enter in the input also saves.
- **Cancel** (icon `close`)
  - Exits edit mode with no changes.

## Videos section

Visibility:

- Shown when either a library is selected OR global search is enabled.

### Search filters

Inputs:

- Artist (text)
- Title (text)
- Tags (comma-separated text)
- Min Duration (number, seconds)
- Max Duration (number, seconds)

Button:

- **Clear Filters**
  - Resets all filter inputs to empty strings.

Filtering behavior:

- Artist filter matches substring against lowercased `video.artist`.
  - Fallback (legacy): if `video.artist` is missing, match against `video.director`.
- Title filter matches substring against `video.title` or `video.name`.
- Tags filter splits by commas and checks if any video tag contains any search token.
- Duration min/max compares against numeric `video.duration` (defaulting to 0 when missing).

Tag sources:

- `video.tags` is populated from the `.nfo` file when present (e.g. `<Genre>` / `<genre>` entries).
- If no `.nfo` provides tags and the file is `.mp4`/`.m4v`, tags may be read from embedded MP4 metadata under the literal `tags` field/key.
- The MP4 genre tag is not used.

### Video table columns

The video table shows these columns:

- Title
- Artist
  - Display: the first 30 characters of `video.artist` (fallback: `video.director`).
  - The full artist string is still available via the cell tooltip/title.
- Album (series)
- Duration
- Tags
- Actions

### Thumbnails

Videos may have an associated thumbnail image.

- The video list response includes `has_thumbnail: boolean` and `media_id: string`.
- When `has_thumbnail` is true, the UI should fetch the image via `GET /api/video/thumbnail/by-id/{media_id}`.
- Fallback: `POST /api/video/thumbnail` with `{ "media_id": "<id>" }`.
- Legacy: `GET /api/video/thumbnail/<...>` no longer accepts file paths; it only accepts a `media_id`.
- The thumbnail image is served directly as an `image/*` response (not JSON) and is read from the backend cache/database.

### Selection controls

- Each row has a checkbox that toggles selection for that video `media_id`.
- A "Select All (N video(s))" checkbox:
  - If checked when not all are selected, selects all currently filtered videos.
  - If checked when all are selected, clears selection.

### Bulk actions

When `selectedVideos.size > 0`, show:

- **Create Playlist (N)** (opens modal)
  - Visible to: any **logged-in** user.
- **Add to Playlist (N)**
  - Opens the "Add Selected Videos to Playlist" modal.
  - Visible to: any **logged-in** user.
- **Add to Current Playlist (N)**
  - POST `/api/video/playback/add-videos` with `{ media_ids: <selected media ids> }`.
  - On success: `alert('Added X video(s) to current playlist...')` and clears selection.
  - On failure: `alert('Failed to add videos to current playlist')`.

### Video table actions

Per video row, Actions column:

- **Add to playlist** button (icon `playlist_add`)
  - On click:
    - Sets `videoToAdd` to that video.
    - Opens the "Add Video to Playlist" modal.
  - Disabled when:
    - the user is not logged in, OR
    - `playlistFolder` is not configured, OR
    - there are zero available playlists.
  - Tooltip/title:
    - "Login required" if not logged in
    - "Configure playlist folder first" if playlistFolder is missing
    - "Create a playlist first" if no playlists exist
    - "Add to playlist" otherwise

- **Add to current playlist** button (icon `queue_music`)
  - POST `/api/video/playback/add-videos` with `{ "media_ids": [<video media id>] }`.
  - Disabled when the video has no `media_id`.

### Row click details popup

- Clicking a table row opens the same details popup used by the Video Explorer page.
- Clicking the row checkbox or action buttons does not open the popup.
- Popup action:
  - **Save** persists editable `Rating` (0–10) and tags:
    - POST `/api/video/metadata/user` with `{ "media_id": <video media id>, "user_rating": <0–10 or null>, "tags": ["..."] }`.
    - Save requires authentication.
    - Persisting prefers `.nfo` when present; otherwise it falls back to embedded MP4 tags (MP4/M4V only).
    - On success, the table reflects updated tags immediately.
  - **Play** triggers POST `/api/video/playback/play-video` with `{ "media_id": <video media id> }`.

## Empty states

- If there are no videos at all: show "No videos found".
- If videos exist but filters remove all: show "No videos match your search criteria".

## Error handling

- Many failures are handled with `console.error` plus `alert()` messages (as noted above).
- Requirements should not add extra UI beyond these existing alerts.
