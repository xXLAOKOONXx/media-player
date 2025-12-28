# Frontend View Requirements

This folder contains per-view (per-tab) UI requirements for the frontend.

Views (tabs in `frontend/src/App.tsx`):

- [Player](player.md)
- [Track Times](track-times.md)
- [Playlists](playlists.md)
- [Music](music.md)
- [Sound Effects](sound-effects.md)
- [Storage](storage.md)

## Note for Copilot (living documentation)

Treat the files in `docs/requirements/` as a description of the **current implemented behavior** of the app.

- When you change frontend/backend code in a way that changes user-visible behavior (buttons, controls, validation, API calls, empty states, enabled/disabled logic, etc.), update the corresponding Markdown file(s) in this folder in the same change.
- When you add a new view/tab or add a new user-facing feature to an existing view, add/update the appropriate requirements file so the folder stays complete and accurate.
- If implementation and docs disagree, prefer updating the docs to match the implementation as part of the same PR.
