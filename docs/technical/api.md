# API Documentation

This document describes the REST API endpoints provided by the Media Player backend.

## Base URL

### Audio API
```
http://localhost:5000/api/audio
```

For Raspberry Pi deployment:
```
http://raspberrypi.local:5000/api/audio
```

**Note:** All API endpoints are under the `/api/audio/*` prefix.

### Video API
```
http://localhost:5000/api/video
```

## Frontend Routes

The application supports URL-based navigation:

- `/` - Redirects to `/audio/player`
- `/audio/player` - Player view
- `/audio/tracks` - Track Times editor
- `/audio/playlists` - Playlist management
- `/audio/music` - Music library
- `/audio/soundeffects` - Sound effects
- `/audio/storage` - Storage management
- `/video` - Video player (under construction)

## Authentication

Currently, the API does not require authentication. In a production environment, you should add authentication mechanisms.

## Endpoints

### Video Library

#### Get Videos in a Video Library

```http
GET /video/libraries/:id/videos
```

Each returned video includes playback stats fields (`playcount`, `last_played`) and a computed `promotion_score`.

### Network Storage Management

#### Get All Storages

```http
GET /audio/storage
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "NAS Music",
    "type": "smb",
    "host": "192.168.1.100",
    "share": "music",
    "username": "user",
    "mount_point": "/mnt/media_1"
  }
]
```

#### Add New Storage

```http
POST /audio/storage
Content-Type: application/json

{
  "name": "NAS Music",
  "type": "smb",
  "host": "192.168.1.100",
  "share": "music",
  "username": "user",
  "password": "password",
  "mount_point": "/mnt/media_1"
}
```

**Response:**
```json
{
  "id": 1,
  "name": "NAS Music",
  "type": "smb",
  "host": "192.168.1.100",
  "share": "music",
  "username": "user",
  "mount_point": "/mnt/media_1"
}
```

#### Delete Storage

```http
DELETE /audio/storage/:id
```

**Response:** 204 No Content

---

### Library Management

#### Get All Libraries

```http
GET /audio/libraries
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Playlists",
    "type": "playlist",
    "path": "/mnt/media_1/playlists",
    "storage_id": 1
  }
]
```

#### Add New Library

```http
POST /libraries
Content-Type: application/json

{
  "name": "Playlists",
  "type": "playlist",
  "path": "/mnt/media_1/playlists",
  "storage_id": 1
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Playlists",
  "type": "playlist",
  "path": "/mnt/media_1/playlists",
  "storage_id": 1
}
```

#### Get Playlists in Library

```http
GET /libraries/:id/playlists
```

**Response:**
```json
[
  {
    "name": "Rock Classics",
    "path": "/mnt/media_1/playlists/rock_classics.m3u",
    "size": 1024
  },
  {
    "name": "Jazz Collection",
    "path": "/mnt/media_1/playlists/jazz.m3u",
    "size": 2048
  }
]
```

---

### Playback Control

#### Play / Resume

Start playback of a playlist or resume paused playback.

```http
POST /playback/play
Content-Type: application/json

{
  "playlist_path": "/path/to/playlist.m3u",
  "track_index": 0
}
```

To resume paused playback:
```http
POST /playback/play
Content-Type: application/json

{}
```

**Response:**
```json
{
  "status": "playing",
  "track_index": 0
}
```

#### Pause

```http
POST /playback/pause
```

**Response:**
```json
{
  "status": "paused"
}
```

#### Stop

```http
POST /playback/stop
```

**Response:**
```json
{
  "status": "stopped"
}
```

#### Next Track

```http
POST /playback/next
```

**Response:**
```json
{
  "status": "playing"
}
```

#### Previous Track

```http
POST /playback/previous
```

**Response:**
```json
{
  "status": "playing"
}
```

#### Set Volume

```http
POST /playback/volume
Content-Type: application/json

{
  "volume": 75
}
```

Volume range: 0-100

**Response:**
```json
{
  "volume": 75
}
```

#### Get Playback Status

```http
GET /playback/status
```

**Response:**
```json
{
  "is_playing": true,
  "is_paused": false,
  "volume": 75,
  "playlist_length": 15,
  "current_track_index": 3,
  "current_track": {
    "title": "Song Title - Artist",
    "path": "/path/to/track.mp3",
    "duration": "180"
  }
}
```

---

### File System

#### Browse Path

Browse a filesystem path to select directories or files.

```http
POST /browse
Content-Type: application/json

{
  "path": "/mnt/media_1"
}
```

**Response:**
```json
{
  "current_path": "/mnt/media_1",
  "items": [
    {
      "name": "playlists",
      "path": "/mnt/media_1/playlists",
      "is_directory": true,
      "is_playlist": false
    },
    {
      "name": "rock.m3u",
      "path": "/mnt/media_1/rock.m3u",
      "is_directory": false,
      "is_playlist": true
    }
  ]
}
```

### Crossfade Configuration

#### Get Crossfade Configuration

```http
GET /audio/crossfade/config
```

**Response:**
```json
{
  "enabled": true,
  "duration_ms": 3000,
  "fade_out_start_before_end_ms": 5000
}
```

**Response Fields:**
- `enabled` (boolean) - Whether crossfading is enabled
- `duration_ms` (number) - Fade duration in milliseconds
- `fade_out_start_before_end_ms` (number) - When to start fading before track ends

#### Update Crossfade Configuration

```http
PUT /audio/crossfade/config
Content-Type: application/json

{
  "enabled": true,
  "duration_ms": 4000,
  "fade_out_start_before_end_ms": 6000
}
```

**Request Body:**
- `enabled` (boolean, optional) - Enable/disable crossfading
- `duration_ms` (number, optional) - Fade duration in milliseconds (must be >= 0)
- `fade_out_start_before_end_ms` (number, optional) - When to start fading (must be >= 0)

**Response:**
```json
{
  "enabled": true,
  "duration_ms": 4000,
  "fade_out_start_before_end_ms": 6000
}
```

**Example - Enable crossfading:**
```bash
curl -X PUT http://localhost:5000/api/crossfade/config \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'
```

**Example - Adjust fade duration:**
```bash
curl -X PUT http://localhost:5000/api/crossfade/config \
  -H "Content-Type: application/json" \
  -d '{"duration_ms": 5000, "fade_out_start_before_end_ms": 8000}'
```

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "error": "Error message description"
}
```

Common HTTP status codes:
- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `204 No Content` - Request successful, no content to return
- `400 Bad Request` - Invalid request data
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## M3U Playlist Format

The application supports M3U and M3U8 playlist formats:

```
#EXTM3U
#EXTINF:180,Artist - Song Title
/path/to/song1.mp3
#EXTINF:240,Another Artist - Another Song
/path/to/song2.mp3
```

- Lines starting with `#` are metadata
- `#EXTM3U` indicates extended M3U format
- `#EXTINF:duration,artist - title` provides track information
- File paths can be absolute or relative to the playlist location

## Server-Sent Events (SSE) Support

The Media Player uses Server-Sent Events (SSE) for real-time status updates, providing reliable one-way communication from server to client.

### Connection

SSE endpoints are available at:
- **Audio Status**: `/api/audio/playback/events`
- **Video Status**: `/api/video/playback/events`

SSE uses standard HTTP, making it more reliable than WebSockets and compatible with all modern browsers through the native `EventSource` API.

### Benefits of SSE

- **Built-in reconnection**: Browser automatically handles connection drops
- **HTTP-based**: Works through proxies and firewalls better than WebSockets
- **No library needed**: Native browser support via `EventSource`
- **Simpler**: Standard HTTP responses with `text/event-stream` content type
- **Efficient**: Server pushes updates only when state changes

### Status Update Events

#### Audio Status Updates

**Endpoint:** `GET /api/audio/playback/events`

The server streams audio playback status updates whenever there is a state change (play, pause, stop, volume change, track change, etc.).

**Event Data:**
```json
{
  "is_playing": true,
  "is_paused": false,
  "volume": 75,
  "playlist_length": 15,
  "current_track_index": 3,
  "current_track": {
    "title": "Song Title - Artist",
    "path": "/path/to/track.mp3",
    "duration": "180",
    "start_time": null,
    "end_time": null,
    "artist": "Artist Name",
    "album": "Album Name"
  },
  "next_track": {
    "title": "Next Song - Artist",
    "artist": "Artist Name",
    "album": "Album Name"
  },
  "shuffle": false,
  "repeat_mode": "none",
  "current_position": 45.5
}
```

#### Video Status Updates

**Endpoint:** `GET /api/video/playback/events`

The server streams video playback status updates whenever there is a state change.

**Event Data:**
```json
{
  "is_playing": true,
  "is_paused": false,
  "current_track": {
    "title": "Video Title",
    "path": "/path/to/video.mp4",
    "duration": 3600
  },
  "next_track": {
    "title": "Next Video"
  },
  "current_track_index": 0,
  "playlist_length": 10,
  "volume": 50,
  "shuffle": false,
  "repeat_mode": "none",
  "current_position": 120.5,
  "audio_tracks": [...],
  "subtitle_tracks": [...],
  "current_audio_track_id": 1,
  "current_subtitle_track_id": 2
}
```

### Client Example

Using native `EventSource` API in JavaScript/TypeScript:

```typescript
// Connect to audio status stream
const audioEventSource = new EventSource('/api/audio/playback/events');

audioEventSource.onopen = () => {
  console.log('Connected to audio status stream');
};

audioEventSource.onmessage = (event) => {
  const status = JSON.parse(event.data);
  console.log('Audio status update:', status);
  // Update UI with new status
};

audioEventSource.onerror = (error) => {
  console.error('SSE error:', error);
  // Browser will automatically attempt to reconnect
};

// Connect to video status stream
const videoEventSource = new EventSource('/api/video/playback/events');

videoEventSource.onmessage = (event) => {
  const status = JSON.parse(event.data);
  console.log('Video status update:', status);
  // Update UI with new status
};

// Close connections when done
// audioEventSource.close();
// videoEventSource.close();
```

### Migration from Polling

Previous implementations used REST polling every second:
```typescript
// Old approach (deprecated)
setInterval(() => {
  fetch('/api/audio/playback/status')
    .then(res => res.json())
    .then(status => updateUI(status));
}, 1000);
```

The new SSE approach provides:
- **Real-time updates**: Changes are pushed immediately, not polled
- **Reduced latency**: No waiting for the next poll interval
- **Lower network overhead**: Single persistent HTTP connection instead of repeated requests
- **Better scalability**: Server pushes only when state changes
- **Automatic reconnection**: Browser handles connection recovery

The REST endpoints (`/api/audio/playback/status` and `/api/video/playback/status`) remain available for initial status fetching or as a fallback.