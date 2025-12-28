# Login View Requirements

URL: `/login`

Source component:
- `frontend/src/components/Login.tsx`

## Purpose

Provides user authentication before accessing the media player application.

## Access

The Login view is displayed when:
- User is not authenticated
- User navigates to any route while not authenticated
- After logout

## Layout

The Login view is a centered modal-style interface with:

### User Selection

1. **User dropdown** (select element)
   - Label: "Select User:"
   - Options:
     - Default option: "-- Select a user --"
     - All available users with format: `{username} ({role})`
     - Example: "admin (admin)", "default (default)", "john (custom)"
   - Required to proceed
   - Disabled while logging in

### Password Input (Conditional)

2. **Password field** (input type="password")
   - Only displayed when admin user is selected
   - Label: "Password (optional for admin):"
   - Placeholder: "Leave empty if no password is set"
   - Optional field
   - Disabled while logging in
   - Note: Admin user may have no password initially, making this field truly optional

### Actions

3. **Login button**
   - Label: "Login"
   - Changes to "Logging in..." while processing
   - Disabled when:
     - No user is selected
     - Login is in progress
   - On click:
     - Sends POST request to `/api/auth/login` with username and password
     - On success: redirects to `/audio/player`
     - On failure: displays error message

### Information

4. **Info text**
   - Message: "Default user has restricted access. Admin can manage settings and users."
   - Displayed at bottom of login box
   - Styled in gray color

## User Roles

### Default User
- Username: "default"
- Password: None (cannot be set)
- Access:
  - Can use playback controls (play, pause, stop, next, previous, volume, shuffle, repeat)
  - Can view playlists, music libraries, sound effects, and video libraries
  - Can view current playback status
  - **Cannot** add/edit/delete storage locations
  - **Cannot** add/edit/delete playlist folders
  - **Cannot** add/edit/delete music libraries
  - **Cannot** add/edit/delete sound effects folders
  - **Cannot** add/edit/delete video libraries
  - **Cannot** browse filesystem
  - **Cannot** change settings
  - **Cannot** manage users

### Admin User
- Username: "admin"
- Password: Optional (can be set by admin)
- Access:
  - Full access to all features
  - Can add/edit/delete all resources
  - Can browse filesystem
  - Can change all settings
  - Can manage users:
    - Create custom users
    - Delete custom users
    - Set/change admin password

### Custom Users
- Username: User-defined
- Password: Optional
- Access: Same as default user (restricted access)
- Can be created and deleted by admin

## Error Handling

### Error display
- Displayed in red box above login button
- Shows server error messages or generic errors
- Examples:
  - "Please select a user"
  - "Invalid username or password"
  - "Failed to connect to server"

### Loading State
- Shows "Loading..." message while fetching available users
- Entire form hidden until users are loaded

## API Endpoints Used

### GET `/api/users` (Optional)
- Fetches list of available users for dropdown
- On error or 401/403: falls back to default system users (admin, default)
- Returns:
```json
[
  {"id": 1, "username": "admin", "role": "admin"},
  {"id": 2, "username": "default", "role": "default"},
  {"id": 3, "username": "john", "role": "custom"}
]
```

### POST `/api/auth/login`
- Authenticates user and creates session
- Request body:
```json
{
  "username": "admin",
  "password": ""
}
```
- On success: Sets session cookie and returns user info
- Response:
```json
{
  "id": 1,
  "username": "admin",
  "role": "admin"
}
```

## Styling

- Centered modal on gradient purple background
- White card with rounded corners and shadow
- Responsive design for mobile devices
- Material icons for branding
- Purple gradient theme matching app design

## Security Notes

- Passwords transmitted over HTTPS in production
- Session cookies set with `httponly` flag for security
- Session expires after 30 days of inactivity
- Default user intentionally has no password (by design)
- Admin password is optional but recommended for production use
