# Settings View Requirements

URLs: `/audio/settings` and `/video/settings`

Source component:
- `frontend/src/components/SettingsManager.tsx`

## Purpose

Provides a centralized location for configuring all application settings, including audio crossfade settings and video playback preferences.

## Access

The Settings view is accessible from both:
- Audio page: `/audio/settings` - via the "Settings" tab in the audio navigation
- Video page: `/video/settings` - via the "Settings" tab in the video navigation

Both routes display the same Settings component with all configuration options.

## Layout

The Settings view is divided into sections:

### Audio Settings Section

Contains configuration options for audio playback.

#### Crossfade Group

1. **Enable crossfade between tracks** (checkbox)
   - Default: enabled (checked)
   - When disabled, all other crossfade options are disabled

2. **Crossfade duration (ms)** (number input)
   - Range: 0 or greater
   - Step: 100
   - Default: 3000
   - Description: "How long the fade effect between tracks should last"
   - Only editable when crossfade is enabled

3. **Start fade before track end (ms)** (number input)
   - Range: 0 or greater
   - Step: 100
   - Default: 5000
   - Description: "When to start fading out the current track before it ends"
   - Only editable when crossfade is enabled

### Video Settings Section

Contains configuration options for video playback.

#### Playback Group

1. **Open videos in fullscreen mode** (checkbox)
   - Default: enabled (checked)
   - Description: "When enabled, videos will automatically play in fullscreen"

2. **Preferred screen** (dropdown)
   - Options:
     - "None (use default)" - value: null
     - "Screen 0 (Primary)" - value: 0
     - "Screen 1" - value: 1
     - "Screen 2" - value: 2
     - "Screen 3" - value: 3
   - Default: None (use default)
   - Description: "Which screen to display videos on (if multiple displays are available)"

### Statistics Settings Section (Admin Only)

Contains configuration options for playback statistics recording.

#### Playback Statistics Group

1. **Stats database folder** (text input with Browse button)
   - Default: empty string (uses backend directory as default location)
   - Description: "Folder where the media-player-stats.db file will be stored. Leave empty to use the default location (backend directory)."
   - Browse button: Opens folder browser dialog
   - When folder is set or left empty:
     - Application creates `media-player-stats.db` in the specified folder (or backend directory if empty)
     - Records playback statistics when media is played for 50% or 5 minutes (whichever is smaller)
     - Each entry contains: timestamp, absolute folder path, current username

## Actions

### Save Settings Button

Located at the bottom of the page:
- Label: "Save Settings"
- On click:
  - Sends PUT request to `/api/settings` with all current settings
  - On success: displays alert "Settings saved successfully!"
  - On failure: displays alert with error message
- While saving:
  - Button is disabled
  - Label changes to "Saving..."

## Loading Behavior

On mount:
- Displays "Loading settings..." message
- Sends GET request to `/api/settings`
- Populates all form fields with retrieved settings
- Removes loading message and shows the form

## API Endpoints Used

### GET `/api/settings`

Retrieves all current settings.

Response format:
```json
{
  "crossfade": {
    "enabled": true,
    "duration_ms": 3000,
    "fade_out_start_before_end_ms": 5000
  },
  "video": {
    "fullscreen": true,
    "preferred_screen": null
  },
  "stats_folder": ""
}
```

### PUT `/api/settings`

Updates settings with the provided values.

Request format: Same as GET response

Returns updated settings on success, or error object on failure.

## Validation

Client-side:
- Number inputs enforce minimum value of 0
- Number inputs use step of 100 for user convenience
- Stats folder must be a string (can be empty)

Server-side:
- `crossfade.enabled` must be boolean
- `crossfade.duration_ms` must be non-negative number
- `crossfade.fade_out_start_before_end_ms` must be non-negative number
- `video.fullscreen` must be boolean
- `video.preferred_screen` must be null, number, or string
- `stats_folder` must be a string

## Error Handling

- Loading errors: logged to console, form not displayed
- Save errors: displayed to user via alert with error message
- Network errors: displayed to user via generic error message

## Styling

The Settings view follows the application's design system:
- Uses standard form inputs and labels
- Sections are contained in cards with subtle shadows
- Responsive layout that centers content and limits maximum width
- Follows dark mode color scheme when applicable
- Disabled inputs show reduced opacity

## User Management Section (Admin Only)

Visible only when logged in as admin user.

### Existing Users Table

Displays all users in the system:

| Column | Description |
|--------|-------------|
| Username | The user's login name |
| Role | User role (admin, default, or custom) |
| Actions | Delete button for custom users, "System User" label for admin/default |

- System users (admin, default) cannot be deleted
- Only custom users can be deleted
- Delete button confirms before deletion

### Create New User Form

Initially hidden, shown when "+ Create User" button is clicked.

**Fields:**
1. **Username** (required)
   - Text input
   - Must be unique
   - Cannot be empty

2. **Password** (optional)
   - Password input
   - Placeholder: "Leave empty for no password"
   - User can login without password if left empty

**Actions:**
- **Create button**: Creates the user with role "custom"
- **Cancel button**: Hides the form without creating user

**Validation:**
- Prevents creating additional admin or default users
- Shows error if username already exists
- Shows error on server failure

### Admin Password Management

Initially hidden, shown when "Change Admin Password" button is clicked.

**Fields:**
1. **New Admin Password** (optional)
   - Password input
   - Placeholder: "Leave empty to remove password"
   - Can be set to empty to remove password requirement

**Actions:**
- **Update Password button**: Updates admin user password
- **Cancel button**: Hides the form without updating

**Behavior:**
- Only affects the admin user's password
- Can set or remove password
- Changes take effect immediately

### API Endpoints Used

#### GET `/api/users` (admin only)
Returns list of all users with id, username, and role.

#### POST `/api/users` (admin only)
Creates a new custom user.

Request:
```json
{
  "username": "john",
  "password": "optional_password",
  "role": "custom"
}
```

Returns created user or error message.

#### DELETE `/api/users/:id` (admin only)
Deletes a user by ID. Cannot delete admin or default users.

#### PUT `/api/users/:id/password` (admin only)
Updates a user's password. Only allowed for admin user.

Request:
```json
{
  "password": "new_password_or_null"
}
```

## Access Control

- Settings page is accessible to all authenticated users
- Video and audio settings sections visible to all users
- User Management section only visible to admin role
- Non-admin users cannot see or access user management features
- All modification endpoints protected by admin-only decorators
