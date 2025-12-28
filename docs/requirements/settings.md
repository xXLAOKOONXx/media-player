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
  }
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

Server-side:
- `crossfade.enabled` must be boolean
- `crossfade.duration_ms` must be non-negative number
- `crossfade.fade_out_start_before_end_ms` must be non-negative number
- `video.fullscreen` must be boolean
- `video.preferred_screen` must be null, number, or string

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
