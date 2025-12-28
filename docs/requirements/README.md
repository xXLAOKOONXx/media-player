# Frontend View Requirements

This folder contains per-view UI requirements for the frontend.

## URL Structure

The application now uses URL-based navigation:

### Audio Routes
- [`/audio/player`](player.md) - Player view with playback controls
- [`/audio/tracks`](track-times.md) - Track Times editor
- [`/audio/playlists`](playlists.md) - Playlist management
- [`/audio/music`](music.md) - Music library
- [`/audio/soundeffects`](sound-effects.md) - Sound effects
- [`/audio/storage`](storage.md) - Storage management
- [`/audio/settings`](settings.md) - Application settings

### Video Routes
- [`/video/player`](video-player.md) - Video player view with playback controls
- [`/video/playlists`](video.md#playlists-tab) - Video playlist management
- [`/video/library`](video-library.md) - Video library management
- [`/video/settings`](settings.md) - Application settings
- [`/video`](video.md) - Video main page (redirects to `/video/player`)

### Default Routes
- `/` - Redirects to `/audio/player`

## Note for Copilot (living documentation)

Treat the files in `docs/requirements/` as a description of the **current implemented behavior** of the app.

- When you change frontend/backend code in a way that changes user-visible behavior (buttons, controls, validation, API calls, empty states, enabled/disabled logic, etc.), update the corresponding Markdown file(s) in this folder in the same change.
- When you add a new view/tab or add a new user-facing feature to an existing view, add/update the appropriate requirements file so the folder stays complete and accurate.
- If implementation and docs disagree, prefer updating the docs to match the implementation as part of the same PR.
