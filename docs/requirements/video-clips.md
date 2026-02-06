# Video Clips View Requirements

URL: `/video/clips`

Source components:
- `frontend/src/components/ClipsManager.tsx`
- `frontend/src/components/ClipsManager.css`

## Purpose

The Video Clips view allows users to view, play, and manage 60-second video clips created from the Player tab.

## Layout

The view contains two main cards:
- **Clips Header** card (description and folder configuration)
- **Clips List** card (grid of created clips)

## Clips Header Card

### Description Section

Shows:
- Title: "Video Clips"
- Description: "Manage your 60-second video clips created from the Player tab."

### Clips Folder Configuration

UI:
- Shows the current clips folder path
- **Edit** button to change the folder path
- When editing:
  - Text input for new folder path
  - **Save** button to save the new path
  - **Cancel** button to cancel editing

Behavior:
- GET `/api/video/clips/folder` to retrieve current folder path
- PUT `/api/video/clips/folder` with `{ "folder": "<path>" }` to update folder path
- The backend creates the folder if it doesn't exist
- Default folder is `<app_data_dir>/clips`

## Clips List Card

### Empty State

When no clips exist:
- Show scissors icon
- Show text "No clips yet"
- Show hint: "Go to the Player tab and click the scissors icon to create a 60-second clip"

### Loading State

While loading clips:
- Show spinning refresh icon
- Show text "Loading clips..."

### Error State

When loading fails:
- Show error icon
- Show error message

### Clips Grid

When clips exist:
- Show clips count in header: "Your Clips (N)"
- Display clips in a responsive grid:
  - Desktop: multiple columns (auto-fill, min 300px per card)
  - Mobile: single column

#### Clip Card

Each clip card displays:
- **Header**:
  - Scissors icon
  - Clip filename
  - Series name badge (if source is part of a series)
    - Shows TV icon + series name
- **Details**:
  - Duration (formatted as M:SS)
  - Source position (formatted as M:SS) - the playback position when clip was created
  - Creation date and time
- **Actions**:
  - **Play** button (primary)
    - Opens clip in new tab via `/api/video/clips/stream/<clip_media_id>`
  - **Delete** button (danger)
    - Shows confirmation dialog
    - DELETE `/api/video/clips/<clip_media_id>` to delete clip
    - Reloads clips list after successful deletion

### Visual Styling

- Cards have hover effect (translate up, add shadow)
- Details use material icons for visual consistency
- Series badge has subtle background
- Actions use flex layout for equal button width

## Clip Creation (from Player Tab)

A "Create Clip" button is added to the Video Player tab (see `video-player.md`):
- Located in the title actions area, next to the Like/Rate button
- Shows scissors icon (content_cut)
- Shows hourglass icon while creating clip
- Disabled when no video is playing or media_id is missing
- Mobile-friendly with adequate touch target size

Behavior:
- Clicking the button calls POST `/api/video/clips/create`
- The backend:
  - Creates a 60-second clip of the previous 60 seconds from current playback position
  - Uses the same audio and subtitle tracks as currently selected
  - Embeds a thumbnail in the MP4 file
  - Stores metadata including source video, series name (if applicable), and creation time
  - Saves the clip in the configured clips folder
  - Stores clip metadata in the `video_clips` database table
- Shows success/error message for 5 seconds
- Success message: "Clip created successfully!"
- Error message includes error details

## API Endpoints

### List Clips
- **GET** `/api/video/clips`
- Query params:
  - `user_id` (optional): Filter clips by user
- Response: `{ "clips": [<clip_objects>] }`
- Authentication: Required

### Create Clip
- **POST** `/api/video/clips/create`
- Body: none (uses current playback state)
- Response: `{ "clip_media_id": "...", "clip_file_path": "...", ... }`
- Authentication: Required
- Requirements:
  - Video must be currently playing
  - Source video file must exist

### Get Clip
- **GET** `/api/video/clips/<clip_media_id>`
- Response: `<clip_object>`
- Authentication: Required

### Delete Clip
- **DELETE** `/api/video/clips/<clip_media_id>`
- Response: `{ "success": true }`
- Authentication: Required

### Stream Clip
- **GET** `/api/video/clips/stream/<clip_media_id>`
- Response: Video stream (MP4)
- Authentication: Required

### Get Clips Folder
- **GET** `/api/video/clips/folder`
- Response: `{ "folder": "<path>" }`
- Authentication: Required

### Set Clips Folder
- **PUT** `/api/video/clips/folder`
- Body: `{ "folder": "<path>" }`
- Response: `{ "success": true, "folder": "<path>" }`
- Authentication: Required

## Database Schema

The `video_clips` table stores clip metadata:
- `id`: Primary key
- `clip_media_id`: Unique media ID (SHA256 hash of clip path)
- `source_media_id`: Media ID of source video
- `source_file_path`: Path to source video file
- `source_series_name`: Series name if source is part of a series
- `clip_file_path`: Path to clip file
- `clip_file_name`: Clip filename
- `clip_duration`: Duration in seconds
- `source_position`: Playback position when clip was created (in seconds)
- `created_at`: Creation timestamp
- `user_id`: ID of user who created the clip
- `audio_track_id`: Audio track ID used in clip
- `subtitle_track_id`: Subtitle track ID used in clip

## Technical Implementation

### Backend (Python/Flask)

Clip creation uses ffmpeg:
- Extract 60 seconds starting from (current_position - 60)
- Use libx264 codec for video (CRF 23, medium preset)
- Use AAC codec for audio (128k bitrate)
- Map specific audio track if selected
- Map specific subtitle track if selected
- Embed metadata (source media_id, series name, creation time)
- Generate thumbnail at 1 second into clip
- Embed thumbnail as attached picture in MP4

Service: `backend/services/video/clip_manager.py`

### Frontend (React/TypeScript)

Components:
- `ClipsManager.tsx`: Main clips management component
- `VideoPlayer.tsx`: Extended with clip creation button

Features:
- Real-time clip creation feedback
- Responsive grid layout
- Clip playback in new tab
- Folder configuration
- Clip deletion with confirmation

## Error Handling

Backend errors are logged to console and displayed to user:
- "No video currently playing" (400)
- "Source video file not found" (404)
- "Failed to create clip" (500)
- "ffmpeg is not available" (500)

Frontend displays error messages inline for 5 seconds.

## Security

- All clip endpoints require authentication
- Clip files are served through authenticated endpoints only
- User can only see their own clips (filter by user_id)
- File paths are validated to prevent path traversal
