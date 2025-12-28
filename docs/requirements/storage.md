# Storage View Requirements

URL: `/audio/storage`

Source component:
- `frontend/src/components/StorageManager.tsx`

## Purpose

Allows configuring and deleting network storage locations (SMB/CIFS or NFS).

## Data loading

- On mount, fetch `/api/audio/storage` and render the list of configured storages.

## Add Storage toggle

Button:
- **+ Add Storage** / **Cancel** toggles display of the add form.

## Add Storage form

Form submission:
- POST `/api/audio/storage` with the full `newStorage` object.
- On success:
  - Reset the form values to defaults.
  - Hide the form.
  - Reload the storage list.

Fields:
- Storage Name (required)
- Type (select):
  - SMB/CIFS (`smb`)
  - NFS (`nfs`)
- Host/Server (required)
- Share Name (required)
- Username (optional)
- Password (optional, `type=password`)
- Mount Point (optional)

Button:
- **Add Storage** (submit)

## Storage list

Empty state:
- “No network storage configured”.

Per storage entry:
- Display:
  - Name
  - Type badge (uppercased)
  - `//{host}/{share}`
  - Username (or `guest` if empty)
  - Mount point

Button:
- **Delete**
  - Prompts confirmation: “Are you sure you want to delete this storage?”
  - If confirmed: DELETE `/api/audio/storage/{id}`.
  - On success: reload storage list.

## Error handling

- Errors are logged to the console.
- No additional UI error messages are shown beyond the confirm prompt.
