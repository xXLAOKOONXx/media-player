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
- Show **Set music_start** and **Set music_end** buttons in the Now Playing title row.
- Show a **Like/Rate** button (icon `thumb_up`) in the Now Playing title row.
- Conditionally show:
  - Custom Range line if either `current_track.start_time` or `current_track.end_time` is not null.

### Set music_start / music_end to current timestamp

UI:
- Two buttons are shown in the Now Playing title row:
  - **Set music_start**
  - **Set music_end**
- Buttons are disabled when `current_track.media_id` is missing.

Behavior:
- Clicking **Set music_start** sends:
  - POST `/api/video/metadata/user` with `{ "media_id": <current_track.media_id>, "start_time_in_ms": <current_position * 1000> }`.
- Clicking **Set music_end** sends:
  - POST `/api/video/metadata/user` with `{ "media_id": <current_track.media_id>, "end_time_in_ms": <current_position * 1000> }`.
- Errors are logged to the console (no toasts/banners).

### Like / Rate current video

- Clicking the **Like/Rate** button opens a modal dialog titled "Rate video".
- The modal allows selecting a rating from 0 to 10 (whole numbers).
- If `current_track.user_rating` is available, the modal preselects that rating (rounded to the nearest whole number).
- Clicking **Save** sends:
  - POST `/api/video/metadata/user` with `{ "media_id": <current_track.media_id>, "user_rating": <0–10> }`.
- The save requires authentication.
- Persisting prefers writing to the video’s `.nfo` file when present; otherwise it falls back to embedded MP4 tags (MP4/M4V only).

Notes:
- The backend enriches playlist entries using the cached video database first (same source as Video Library titles).
  - If the cache does not contain the video, the backend falls back to scraping the video file metadata and its adjacent `.nfo` file (when present).
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
  - Stop also clears the current playlist/queue.
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

### Audio & Subtitles

If the current video has multiple audio tracks and/or multiple subtitle tracks, show dropdowns in the player controls to select them.

Data source:
- `GET /api/video/playback/status` includes:
  - `audio_tracks`: Array of `{ id: number, label: string, selected?: boolean }`
  - `subtitle_tracks`: Array of `{ id: number, label: string, selected?: boolean }` (includes an `Off` option with `id: -1` when subtitles exist)
  - `current_audio_track_id`: number | null
  - `current_subtitle_track_id`: number | null

Label format:
- Track labels are formatted as `title - lang (id)` when both title and lang are available.

UI behavior:
- Show the **Audio** dropdown only when more than 1 audio track is available.
- Show the **Subtitles** dropdown only when more than 1 subtitle track is available.

Default selection behavior:
- If the current video has multiple audio tracks and the user has a preferred language configured, the backend attempts to select an audio track matching that preferred language.
- If multiple audio tracks match the preferred language, the backend prefers a track that is not marked as "visual-impaired".
- If subtitles are currently off and the backend finds a subtitle track whose title (or MPV `metadata.name`) contains "forced" and whose language matches the active audio track language, the backend selects that subtitle track by default.
- If the user explicitly selects a subtitle track (including "Off"), the backend does not override that choice.

Actions:
- Audio selection: POST `/api/video/playback/audio-track` with `{ "track_id": <number> }`.
- Subtitle selection: POST `/api/video/playback/subtitle-track` with `{ "track_id": <number> }`.

### Save Default channels

UI behavior:
- When the current video has more than one selectable audio track and/or more than one selectable subtitle track, show a button **Save Default channels**.

Action:
- Clicking **Save Default channels** sends POST `/api/video/playback/save-default-channels` with an empty JSON body `{}`.

Persistence behavior:
- The backend stores the current audio and subtitle selection for the logged-in user.
- The preference is saved with up to three scopes (when resolvable from the current video's `media_id`):
  - **Video** scope (exact `media_id`)
  - **Season** scope
  - **Series** scope
- Subtitle **Off** is stored as a valid preference.

Auto-select precedence:
- On playback start, stored preferences are applied in this order:
  1) Video
  2) Season
  3) Series
- Preferences are only applied when the user has not already manually selected an audio/subtitle track for the current playback.

## Error handling

- Network errors are logged to the console.
- The UI does not currently display error banners/toasts for these controls; requirements should match this (no extra UX).

## Video Playback Implementation

Video playback is handled client-side in the browser using HTML5 video elements. The backend manages:
- Playlist state and navigation
- Playback status tracking
- Volume level management

The actual video rendering and streaming is done through the browser's native video capabilities.

## Status Updates (WebSocket with REST Fallback)

The Video Player view receives real-time status updates via WebSocket with automatic REST polling fallback:
- **WebSocket Event**: `video_status`
- **Connection**: Established automatically when the VideoPage component mounts
- **Source**: `frontend/src/hooks/useWebSocketStatus.ts` provides the WebSocket hook
- **Updates**: Pushed from server when playback state changes (play, pause, stop, volume, track changes, seek, etc.)
- **Initial Status**: Fetched via REST API (`/api/video/playback/status`) on mount
- **Reconnection**: Automatic reconnection with exponential backoff on connection loss
- **REST Fallback**: If WebSocket connection fails after 3 attempts, automatically switches to REST polling (`/api/video/playback/status`) every 1 second
- **Polling Behavior**: When using REST fallback, the frontend polls the status endpoint continuously until the component unmounts
