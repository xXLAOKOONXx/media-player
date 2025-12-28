# Track Times View Requirements

Source component:
- `frontend/src/components/TrackTimesEditor.tsx`

## Purpose

Allows editing per-track custom start/end times for the currently loaded playlist.

## Data loading

- On mount, fetch `/api/playback/tracks` and populate the track list.
- Auto-refresh every 10 seconds while the document is visible (`!document.hidden`).

## Empty state

When there are no tracks (`tracks.length === 0`):
- Show a card titled “Track Times”.
- Show “No playlist loaded” and “Load a playlist to edit track start and end times”.
- No edit controls are displayed.

## Track list UI

Each track item has two modes: display mode and edit mode.

### Display mode

Shown when `editingTrack !== track.index`.

Displayed fields:
- `#{track.index + 1}: {track.title}`
- Duration label only when `track.duration !== 'Unknown'`: `Duration: {track.duration}s`
- Custom times:
  - If `start_time` or `end_time` is not null: show `📌 Custom: <start> - <end>`.
  - Else: show “No custom times set”.

Buttons:
- **Edit**
  - Enters edit mode for that track.
  - Pre-fills inputs with formatted times (`MM:SS`) derived from existing start/end.
- **Clear** (only visible when start or end time is set)
  - Sends PUT `/api/playback/tracks/{trackIndex}/times` with JSON `{ "start_time": null, "end_time": null }`.
  - On failure: show an `alert()`.
  - On success: reload the track list.

### Edit mode

Shown when `editingTrack === track.index`.

Inputs:
- **Start Time** (text)
  - Placeholder: `0:00 or empty`
  - Accepts `MM:SS` or raw seconds.
  - Empty string means null.
- **End Time** (text)
  - Placeholder: `Leave empty for end`
  - Accepts `MM:SS` or raw seconds.
  - Empty string means null.

Validation rules (must block save and show inline error text):
- Start time must be non-negative.
- End time must be non-negative.
- If both are provided: start must be strictly less than end.

Buttons:
- **Save**
  - Parses the two inputs into seconds.
  - Sends PUT `/api/playback/tracks/{trackIndex}/times` with JSON `{ "start_time": <number|null>, "end_time": <number|null> }`.
  - If response is not OK: show inline error text (prefer server-provided `error` JSON field).
  - On success:
    - Exit edit mode.
    - Clear input state.
    - Reload the track list.
- **Cancel**
  - Exits edit mode without saving.
  - Clears input state and any error text.

## Error handling

- Load errors are logged to the console.
- Save errors show an inline error message.
- Clear errors use `alert()`.
