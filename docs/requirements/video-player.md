# Video Player View Requirements

URL: `/video/player`

Source components:
- `frontend/src/components/VideoPlayer.tsx`
- `frontend/src/components/VideoPlaybackControls.tsx`

## Purpose

The Video Player view displays the currently playing video, playback progress (including seek), "Up Next", and provides transport + mode + volume controls.

## Layout

- The view contains two cards:
  - **Now Playing** card (video info + progress)
  - **Controls** card (shuffle/repeat + transport + volume)

## Now Playing card

### Empty state

When there is no playback status or `status.current_track` is missing:
- Show text "No video playing".
- Show guidance: "Select a playlist from the Video Playlists tab to start playback".
- No progress/seek control is shown.

### Video information display

When a `current_track` exists:
- Show video title (`current_track.title`).
- Show a **play** indicator icon when `status.is_playing` is true AND `status.is_paused` is false.
- Show a **pause** indicator icon when `status.is_paused` is true.
- Conditionally show:
  - Custom Range line if either `current_track.start_time` or `current_track.end_time` is not null.

Notes:
- `current_track.start_time` and `current_track.end_time` can be set either by explicit user edits (track times API) or derived automatically from per-file metadata.
- For MP4/M4V files, the backend recognizes iTunes freeform tags:
  - `----:LAO:music-start` (milliseconds) → `current_track.start_time` (seconds)
  - `----:LAO:music-end` (milliseconds) → `current_track.end_time` (seconds)
- If `current_track.end_time` is set, the backend auto-advances to the next video when the playback position reaches that end time.

### Progress + seeking

Controls:
- A seekable range input (slider) is rendered when an effective duration can be computed.

Behavior:
- The seek slider:
  - Has `min = startTime` (defaults to 0).
  - Has `max = endTime` if present, else video duration, else a fallback (100).
  - Has `step = 0.1`.
  - Uses `value = current_position` (defaults to 0).
  - Is **disabled** when `status.is_playing` is falsy.
- On slider change, send a POST request to `/api/video/playback/seek` with JSON `{ "position": <float> }`.
- Display current time and total time:
  - Current time shows `current_position`.
  - Total time shows `startTime + effectiveDuration` when available; otherwise `--:--`.

### Playlist position

- Show "Video {current_track_index + 1} of {playlist_length}".

### Up Next

- If `status.next_track` exists, show an "Up Next" section with:
  - Next video title.

## Controls card

### Mode controls

#### Shuffle button

UI:
- Icon: `shuffle`.
- Active styling when `status.shuffle` is true.

Behavior:
- Clicking toggles shuffle state.
- POST `/api/video/playback/shuffle` with JSON `{ "enabled": <boolean> }`, where enabled is the toggled value.

#### Repeat button

UI:
- Active styling when `status.repeat_mode !== 'none'`.
- Icon depends on mode:
  - `repeat` when mode is `all` or `none`
  - `repeat_one` when mode is `one`
- Tooltip/title depends on mode:
  - `Repeat: Off` when `none`
  - `Repeat: All` when `all`
  - `Repeat: One` when `one`

Behavior:
- Clicking cycles repeat mode in order: `none → all → one → none`.
- POST `/api/video/playback/repeat` with JSON `{ "mode": <nextMode> }`.

### Transport controls

Buttons:
- **Previous**: POST `/api/video/playback/previous`.
- **Play** or **Pause** (mutually exclusive):
  - Show **Play** when NOT (is_playing && !is_paused).
  - Show **Pause** when (is_playing && !is_paused).
  - Play: POST `/api/video/playback/play` with an empty JSON body `{}`.
  - Pause: POST `/api/video/playback/pause`.
- **Stop**: POST `/api/video/playback/stop`.
- **Next**: POST `/api/video/playback/next`.

After each transport/mode action above, the UI triggers `onUpdate()` to refresh status.

### Volume controls

Controls:
- Decrease button (icon `remove`):
  - Decreases volume by 1.
  - Disabled at 0.
  - Tooltip: "Decrease volume by 1%".
- Increase button (icon `add`):
  - Increases volume by 1.
  - Disabled at 100.
  - Tooltip: "Increase volume by 1%".
- Slider (`type=range`, 0–100):
  - Updates volume to the selected integer value.
- Display current volume as `{volume}%`.

Behavior:
- Any volume change sends POST `/api/video/playback/volume` with JSON `{ "volume": <number> }`.
- The UI updates local slider state immediately before/while the request is in flight.

## Error handling

- Network errors are logged to the console.
- The UI does not currently display error banners/toasts for these controls; requirements should match this (no extra UX).

## Video Playback Implementation

Video playback is handled client-side in the browser using HTML5 video elements. The backend manages:
- Playlist state and navigation
- Playback status tracking
- Volume level management

The actual video rendering and streaming is done through the browser's native video capabilities.
