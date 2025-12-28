# Playlists View Requirements

URL: `/audio/playlists`

Source component:
- `frontend/src/components/PlaylistManager.tsx`

## Purpose

Manages “playlist folder” entries, browses for a folder path, lists playlists found in a selected folder, and starts playback of a selected playlist.

## Playlist Folders card

### Initial load

- On mount, fetch `/api/audio/playlists` to load the list of configured playlist folders.

### Add Playlist Folder toggle

Button:
- **+ Add Playlist Folder** / **Cancel**
  - Clicking toggles `showAddForm`.

### Add form

Fields:
- Folder Name (required text)
- Path (required text)

Buttons:
- **Browse** (type=button)
  - Calls POST `/api/browse` with JSON `{ "path": <current path input or '/'> }`.
  - Shows browse results when items are returned.
- **Add Playlist Folder** (submit)
  - POST `/api/audio/playlists` with JSON `{ name, path, type: 'playlist' }`.
  - On success:
    - Clear the form state.
    - Hide the form.
    - Reload playlist folders.

Browse results behavior:
- Displays “Current: {browsePath}”.
- Each browse item is clickable:
  - If `item.is_directory` is true: browse into that directory.
  - Else: set the Path field to `item.path`.

### Folder list

Empty state:
- If no playlist folders exist, show “No playlist folders configured”.

Selecting a folder:
- Clicking a folder row selects it and triggers load of playlists via GET `/api/audio/playlists/{folderId}/files`.

Folder actions (per folder)

#### Rename

Entry point:
- Pencil button (✏️) starts rename mode.

Rename mode controls:
- Text input prefilled with current name.
- **Save**
  - Validates name is non-empty; otherwise `alert('Name cannot be empty')`.
  - PUT `/api/audio/playlists/{folderId}` with JSON `{ "name": <editName> }`.
  - On success: exit rename mode and reload folder list.
- **Cancel**
  - Exits rename mode with no changes.

#### Delete

- Trash button (🗑️) prompts `confirm('Are you sure you want to delete this playlist folder?')`.
- If confirmed: DELETE `/api/audio/playlists/{folderId}`.
- If the deleted folder was selected, clear selection and the playlists list.
- On failure: `alert('Error deleting playlist folder')`.

## Playlists card

Visibility:
- Only shown when a folder is selected.

Behavior:
- Lists playlist files returned from GET `/api/audio/playlists/{folderId}/files`.

Empty state:
- “No playlists found in this folder”.

Per playlist row:
- Display playlist name + full path.
- Button: **Play**
  - POST `/api/audio/playback/play` with JSON `{ "playlist_path": <playlist.path>, "track_index": 0 }`.
  - On success: `alert('Playlist started!')`.
  - On failure: `alert('Error playing playlist')`.
