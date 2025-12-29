# Music View Requirements

URL: `/audio/music`

Source component:
- `frontend/src/components/MusicManager.tsx`

## Purpose

Manages music library folders, loads tracks (single-folder or all folders), filters/searches tracks, selects tracks in bulk, and creates/updates playlists from selected tracks.

## Top header actions

Buttons in the “Music Library” header:

1) **Configure Playlist Folder**
- Opens a modal to set the folder used for playlist creation and for listing `.m3u` playlists.

2) **Add Music Folder**
- Opens a modal to add a new music folder to scan.

3) **Search All Folders**
- Switches the view into global search mode.
- Behavior:
  - Sets `globalSearch = true`.
  - Clears `selectedFolder`.
  - Triggers loading tracks from all folders (see Loading behavior).

Conditional buttons (only when at least one track is selected):

4) **Create Playlist (N)**
- Opens the “Create New Playlist” modal.

5) **Add to Current Playlist (N)**
- Sends selected tracks to the currently loaded playback playlist.

## Playlist Folder indicator

When `playlistFolder` is set (non-empty):
- Display a line “Playlist Folder: {playlistFolder}”.

## Loading behavior

### Initial loads

On mount:
- GET `/api/audio/music` to load music folders.
- GET `/api/audio/music/playlists-folder` to load the configured playlist folder.

When `playlistFolder` changes and is non-empty:
- POST `/api/browse` with `{ path: playlistFolder }` and build the list of “available playlists” by selecting items whose names end with `.m3u`.

### Track loading modes

- If a folder is selected: load tracks for that folder:
  - GET `/api/audio/music/{folderId}/tracks`
- Else if global search is enabled: load tracks from all folders:
  - For each folder in `musicFolders`, GET `/api/audio/music/{folderId}/tracks` concurrently.

During loading:
- Show a loading spinner and the text “Loading tracks...”.

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
  - PUT `/api/audio/music/playlists-folder` with `{ path: playlistFolder }`.
  - On success:
    - Close modal.
    - Reload available playlists.
    - `alert('Playlist folder configured successfully!')`.
  - On failure: `alert('Failed to set playlist folder')`.
- **Cancel**
  - Closes modal.
  - Clears browse results.

## Add Music Folder modal

Opens via **Add Music Folder**.

Fields:
- Folder Name (required)
- Folder Path (required)
- Checkbox: “Scan subfolders recursively”

Buttons:
- **Browse**
  - POST `/api/browse` with `{ path: <current input or '/'> }`.
  - Shows directories.
- Browse list includes `..` and directories.
- **Select Current Folder** sets the Folder Path to the current browse path.
- **Add Folder** (submit)
  - POST `/api/audio/music` with `{ name, path, recursive }`.
  - On success: reset form, close modal, reload folder list.
- **Cancel** closes modal and clears browse results.

## Create New Playlist modal

Opens via **Create Playlist (N)**.

Behavior:
- If no tracks are selected, block action with `alert('Please select at least one track')`.
- If `playlistFolder` is not set, block action with `alert('Please configure a playlist folder first')`.

Fields:
- Playlist Name (required)

Buttons:
- **Create Playlist** (submit)
  - POST `/api/audio/music/playlists/create` with:
    - `playlist_name: newPlaylistName`
    - `media_ids: <selected track media_id values>` (derived from the currently filtered list)
  - On success:
    - `alert('Playlist created successfully!')`
    - Close modal
    - Clear selection
    - Reload available playlists
  - On failure: `alert('Failed to create playlist: <server error>')`
- **Cancel** closes the modal.

## Add Track to Playlist modal

Opens via per-track “Add to playlist” action (see Track table).

Controls:
- Playlist select dropdown (required):
  - Default option: “-- Select Playlist --”
  - Options come from `.m3u` files in `playlistFolder`.

Buttons:
- **Add to Playlist** (submit)
  - POST `/api/audio/music/playlists/{selectedPlaylist}/add-track` with `{ media_id: trackToAdd.media_id }`.
  - On success:
    - `alert('Track added to playlist successfully!')`
    - Close modal and clear selection state.
  - On failure: `alert('Failed to add track: <server error>')`
- **Cancel** closes modal and clears modal state.

## Music Folders section

### Collapsing

- “Music Folders” header is clickable.
- Clicking toggles collapsed state.
- Icon switches between `expand_more` (collapsed) and `expand_less` (expanded).

### Folder row selection

- Clicking the folder info area:
  - Sets `selectedFolder = folder.id`
  - Sets `globalSearch = false`
  - Triggers loading tracks for that folder.

### Folder actions

Per folder, when not editing:
- **Refresh** (icon `refresh`, tooltip “Refresh folder”)
  - POST `/api/audio/music/{folderId}/refresh`
  - Then reload tracks (selected folder or global search).
- **Edit** (icon `edit`)
  - Enters inline edit mode and pre-fills name.
- **Delete** (icon `delete`)
  - Confirms: “Are you sure you want to delete this music folder?”
  - DELETE `/api/audio/music/{folderId}`
  - If deleted folder was selected: clear selection and tracks.

Inline edit mode:
- Text input for folder name.
- **Save** (icon `check`)
  - PUT `/api/audio/music/{folderId}` with `{ name: editName }`.
  - Exits edit mode and reloads folder list.
  - Pressing Enter in the input also saves.
- **Cancel** (icon `close`)
  - Exits edit mode with no changes.

## Tracks section

Visibility:
- Shown when either a folder is selected OR global search is enabled.

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
- Artist filter matches substring against lowercased `track.artist`.
- Title filter matches substring against `track.title` or `track.name`.
- Tags filter splits by commas and checks if any track tag contains any search token.
- Duration min/max compares against numeric `track.duration` (defaulting to 0 when missing).

### Selection controls

- Each row has a checkbox that toggles selection for that track `media_id`.
- If a track has no `media_id`, its checkbox is disabled.
- A “Select All (N track(s))” checkbox:
  - Only counts/selects filtered tracks that have a `media_id`.
  - If checked when not all selectable tracks are selected, selects all selectable filtered tracks.
  - If checked when all selectable tracks are selected, clears selection.

### Bulk actions

When `selectedTracks.size > 0`, show:
- **Create Playlist (N)** (opens modal)
- **Add to Current Playlist (N)**
  - POST `/api/audio/playback/add-tracks` with `{ media_ids: <selected track media_ids> }`.
  - On success: `alert('Added X track(s) to current playlist...')` and clears selection.
  - On failure: `alert('Failed to add tracks to current playlist')`.

### Track table actions

Per track row, Actions column:
- **Add to playlist** button (icon `playlist_add`)
  - On click:
    - Sets `trackToAdd` to that track.
    - Opens the “Add Track to Playlist” modal.
  - Disabled when:
    - the track has no `media_id`, OR
    - `playlistFolder` is not configured, OR
    - there are zero available playlists.
  - Tooltip/title:
    - “Track is missing media id” if the track has no `media_id`
    - “Configure playlist folder first” if playlistFolder is missing
    - “Create a playlist first” if no playlists exist
    - “Add to playlist” otherwise

## Empty states

- If there are no tracks at all: show “No tracks found”.
- If tracks exist but filters remove all: show “No tracks match your search criteria”.

## Error handling

- Many failures are handled with `console.error` plus `alert()` messages (as noted above).
- Requirements should not add extra UI beyond these existing alerts.
