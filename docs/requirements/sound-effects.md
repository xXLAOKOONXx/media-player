# Sound Effects View Requirements

URL: `/audio/soundeffects`

Source component:
- `frontend/src/components/SoundEffectsManager.tsx`

## Purpose

Configures folders that contain sound effect audio files and allows playing an effect on demand.

## Sound Effects Folders card

### Initial load

- On mount, fetch `/api/audio/soundeffects` and render the folder list.

### Add Sound Effects Folder toggle

Button:
- **+ Add Sound Effects Folder** / **Cancel** toggles the add form.

### Add form

Fields:
- Folder Name (required)
- Path (required)

Buttons:
- **Browse**
  - POST `/api/browse` with JSON `{ "path": <current path input or '/'> }`.
  - Displays browse results when items are returned.
- **Add Sound Effects Folder** (submit)
  - POST `/api/audio/soundeffects` with JSON `{ name, path }`.
  - On success: clear form state, hide form, reload folder list.

Browse results behavior:
- Shows “Current: {browsePath}”.
- Clicking an item:
  - If `item.is_directory`: browse into it.
  - Else: set Path to the clicked file path.

### Folder list

Empty state:
- “No sound effects folders configured”.

Selecting a folder:
- Clicking a folder selects it and loads files via GET `/api/audio/soundeffects/{folderId}/files`.

Folder actions

#### Rename

- Pencil button (✏️) enters edit mode.
- Edit mode provides:
  - input prefilled with folder name
  - **Save**: PUT `/api/audio/soundeffects/{folderId}` with JSON `{ "name": <editName> }` (requires non-empty name, else alert).
  - **Cancel**: exits edit mode.

#### Delete

- Trash button (🗑️) prompts confirmation.
- If confirmed: DELETE `/api/audio/soundeffects/{folderId}`.
- If deleted folder is selected: clear selection and file list.

## Audio Files card

Visibility:
- Only shown when a folder is selected.

Empty state:
- “No audio files found in this folder” and “Supported formats: MP3, WAV, OGG, FLAC, M4A, AAC”.

Per file row:
- Shows name, extension, approximate KB size.
- Button: **Play**
  - POST `/api/audio/soundeffects/play` with JSON `{ "sound_path": <file.path> }`.
  - On failure: `alert('Error playing sound effect')`.

## Error handling

- Load errors are logged to the console.
- Some failures show `alert()` as described above.
