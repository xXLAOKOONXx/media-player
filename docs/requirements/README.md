# Frontend View Requirements

This folder contains per-view UI requirements for the frontend.

## URL Structure

The application now uses URL-based navigation:

### Authentication Routes
- [`/login`](login.md) - User authentication and login

### Audio Routes
- [`/audio/player`](player.md) - Player view with playback controls
- [`/audio/tracks`](track-times.md) - Track Times editor
- [`/audio/playlists`](playlists.md) - Playlist management
- [`/audio/music`](music.md) - Music library
- [`/audio/soundeffects`](sound-effects.md) - Sound effects
- [`/audio/storage`](storage.md) - Storage management (admin only)
- [`/audio/settings`](settings.md) - Application settings (includes user management for admin)

### Video Routes
- [`/video/player`](video-player.md) - Video player view with playback controls
- [`/video/explorer`](video-explorer.md) - Video Explorer (browse by tags with carousels)
- [`/video/playlists`](video.md#playlists-tab) - Video playlist management
- [`/video/library`](video-library.md) - Video library management
- [`/video/settings`](settings.md) - Application settings (includes user management for admin)
- [`/video`](video.md) - Video main page (redirects to `/video/player`)

### Default Routes
- `/` - Redirects to `/audio/player` if authenticated, `/login` otherwise

## Access Control

All routes except `/login` require authentication. Users are redirected to `/login` if not authenticated.

### Admin-Only Features
- Adding/editing/deleting network storage
- Adding/editing/deleting playlist folders
- Adding/editing/deleting music libraries
- Adding/editing/deleting sound effects folders
- Adding/editing/deleting video libraries
- Browsing filesystem
- Changing application settings
- Managing users

### All Users (Default and Custom)
- Playback controls (play, pause, stop, next, previous, volume, shuffle, repeat, seek)
- Viewing playlists and libraries
- Viewing current playback status
- Playing sound effects

## Note for Copilot (living documentation)

Treat the files in `docs/requirements/` as a description of the **current implemented behavior** of the app.

- When you change frontend/backend code in a way that changes user-visible behavior (buttons, controls, validation, API calls, empty states, enabled/disabled logic, etc.), update the corresponding Markdown file(s) in this folder in the same change.
- When you add a new view/tab or add a new user-facing feature to an existing view, add/update the appropriate requirements file so the folder stays complete and accurate.
- If implementation and docs disagree, prefer updating the docs to match the implementation as part of the same PR.
