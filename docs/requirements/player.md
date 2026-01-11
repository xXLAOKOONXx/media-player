# Player View Requirements

URL: `/audio/player`

Source components:
- `frontend/src/components/NowPlaying.tsx`
- `frontend/src/components/PlaybackControls.tsx`

## Purpose

The Player view displays the currently playing track, playback progress (including seek), “Up Next”, and provides transport + mode + volume controls.

## Layout

- The view contains two cards:
  - **Now Playing** card (track info + progress)
  - **Controls** card (shuffle/repeat + transport + volume)

## Now Playing card

### Empty state

When there is no playback status or `status.current_track` is missing:
- Show text “No track playing”.
- Show guidance: “Select a playlist from the Playlists tab to start playback”.
- No progress/seek control is shown.

### Track information display

When a `current_track` exists:
- Show track title (`current_track.title`).
- Show a **play** indicator icon when `status.is_playing` is true AND `status.is_paused` is false.
- Show a **pause** indicator icon when `status.is_paused` is true.
- Conditionally show:
  - Artist line if `current_track.artist` exists.
  - Album line if `current_track.album` exists.
  - Custom Range line if either `current_track.start_time` or `current_track.end_time` is not null.

### Progress + seeking

Controls:
- A seekable range input (slider) is rendered when an effective duration can be computed.

Behavior:
- The seek slider:
  - Has `min = startTime` (defaults to 0).
  - Has `max = endTime` if present, else track duration, else a fallback (100).
  - Has `step = 0.1`.
  - Uses `value = current_position` (defaults to 0).
  - Is **disabled** when `status.is_playing` is falsy.
- On slider change, send a POST request to `/api/audio/playback/seek` with JSON `{ "position": <float> }`.
- Display current time and total time:
  - Current time shows `current_position`.
  - Total time shows `startTime + effectiveDuration` when available; otherwise `--:--`.

### Playlist position

- Show “Track {current_track_index + 1} of {playlist_length}”.

### Up Next

- If `status.next_track` exists, show an “Up Next” section with:
  - Next track title.
  - Next track artist/album if present.

## Controls card

### Mode controls

#### Shuffle button

UI:
- Icon: `shuffle`.
- Active styling when `status.shuffle` is true.

Behavior:
- Clicking toggles shuffle state.
- POST `/api/audio/playback/shuffle` with JSON `{ "enabled": <boolean> }`, where enabled is the toggled value.

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
- POST `/api/audio/playback/repeat` with JSON `{ "mode": <nextMode> }`.

### Transport controls

Buttons:
- **Previous**: POST `/api/audio/playback/previous`.
- **Play** or **Pause** (mutually exclusive):
  - Show **Play** when NOT (is_playing && !is_paused).
  - Show **Pause** when (is_playing && !is_paused).
  - Play: POST `/api/audio/playback/play` with an empty JSON body `{}`.
  - Pause: POST `/api/audio/playback/pause`.
- **Stop**: POST `/api/audio/playback/stop`.
  - Stop also clears the current playlist/queue.
- **Next**: POST `/api/audio/playback/next`.

After each transport/mode action above, the UI triggers `onUpdate()` to refresh status.

### Volume controls

Controls:
- Decrease button (icon `remove`):
  - Decreases volume by 1.
  - Disabled at 0.
  - Tooltip: “Decrease volume by 1%”.
- Increase button (icon `add`):
  - Increases volume by 1.
  - Disabled at 100.
  - Tooltip: “Increase volume by 1%”.
- Slider (`type=range`, 0–100):
  - Updates volume to the selected integer value.
- Display current volume as `{volume}%`.

Behavior:
- Any volume change sends POST `/api/audio/playback/volume` with JSON `{ "volume": <number> }`.
- The UI updates local slider state immediately before/while the request is in flight.

## Error handling

- Network errors are logged to the console.
- The UI does not currently display error banners/toasts for these controls; requirements should match this (no extra UX).

## Status Updates (WebSocket with REST Fallback)

The Player view receives real-time status updates via WebSocket with automatic REST polling fallback:
- **WebSocket Event**: `audio_status`
- **Connection**: Established automatically when the AudioPage component mounts
- **Source**: `frontend/src/hooks/useWebSocketStatus.ts` provides the WebSocket hook
- **Updates**: Pushed from server when playback state changes (play, pause, stop, volume, track changes, etc.)
- **Initial Status**: Fetched via REST API (`/api/audio/playback/status`) on mount
- **Reconnection**: Automatic reconnection with exponential backoff on connection loss
- **REST Fallback**: If WebSocket connection fails after 3 attempts, automatically switches to REST polling (`/api/audio/playback/status`) every 1 second
- **Polling Behavior**: When using REST fallback, the frontend polls the status endpoint continuously until the component unmounts
