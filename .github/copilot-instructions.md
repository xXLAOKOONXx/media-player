# Copilot Instructions

## Use `docs/requirements/` as the living spec

The Markdown files in `docs/requirements/` describe the **current implemented UI behavior** of the app (per frontend tab/view).

- When you change user-visible behavior in the frontend/backend (buttons, controls, validation, enabled/disabled logic, API calls, empty states, error handling), update the relevant file(s) in `docs/requirements/` in the same change.
- When you add a new view/tab or introduce a new user-facing feature, create/update the corresponding requirements Markdown file so coverage stays complete.
- If implementation and docs disagree, resolve it by updating `docs/requirements/` to match the implementation as part of the same PR.

## Where the views are defined

- Views are linked in the respective files in `docs/requirements/`

## UI Guidance

When adding or modifying UI components, follow the guidelines in `docs/ui-guidance/` to maintain consistency.

## PR Description

When submitting a PR that changes user-visible behavior, include a summary of the changes made to the UI and enhance it with screenshots or screen recordings in the PR description. This helps reviewers understand the impact of the changes.

## Start App

1. To use the example files of this repository set environment variable `MEDIA_PLAYER_APP_DATA_DIR` to the path of `./examples/`
2. Run the script `start-dev.sh`
