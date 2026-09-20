# Video Search View Requirements (`/video/search`)

## Purpose

The Video Search view lets the user find **Series** and **Films** across all
configured video libraries from a single search box.

- A **Series** is an inferred series from the series tree
  (`GET /api/video/libraries/<id>/series`), same as on the Series view.
- A **Film** is a standalone video (`GET /api/video/libraries/<id>/videos`)
  that is **not** part of a series (its `series` field is empty).

Source component:
- `frontend/src/components/VideoSearch.tsx`

## Data loading

- On mount, the view loads every configured library from
  `GET /api/video/libraries`.
- For each library it loads, in parallel:
  - `GET /api/video/libraries/<id>/videos` — films are the videos whose
    `series` field is empty.
  - `GET /api/video/libraries/<id>/series` — the series tree.
- A failure loading a single library does not break the whole search; the other
  libraries still contribute results.
- While loading, the view shows a “Loading library…” indicator.
- If the overall load fails, an error banner is shown.

## Search input

- A single search box is shown at the top with the placeholder
  “Search series and films…”.
- The search box is focused automatically when the view opens.
- A clear (✕) button empties the search box when it contains text.
- Matching is case-insensitive and matches on substrings.

## Results

- Before any text is entered, the view shows: “Type to search for series and
  films.”
- When a query matches nothing, the view shows:
  “No series or films match “<query>”.”
- Otherwise, matching series and films are shown together as a grid of cards.

### What counts as a match

- **Series** match when the query is contained in:
  - the series title, or
  - any of the series’ tags or artists.
- **Films** match when the query is contained in:
  - the film title, or
  - the film description, or
  - any of the film’s tags, its artist, director, series path, or file name.

### Ordering

Results are ordered so that:

1. **Series come before Films.**
2. Within each kind, results are ordered by **where** the query matched:
   1. title matches first,
   2. then description matches,
   3. then other-field matches (tags/artist/director/etc.).
3. Ties are broken alphabetically by title, then by a stable identifier
   (series id/path or film media id/path) to keep ordering deterministic.

## Cards

Cards look and behave like the cards on the Explorer and Series views.

### Series cards

- Show the series cover (or a placeholder icon when there is no cover).
- Show the same watch-status badges as the Series view:
  - a **Play** badge when watching has started but is not complete,
  - an **Eye** badge when the series is fully watched.
- Clicking a series card opens the same **series popup** used on the Series
  view (see [video-series.md](video-series.md)), including seasons, the episode
  carousel, and the Continue watching / Play Random / Play Random Unseen
  actions.

### Film cards

- Show the film thumbnail (or a placeholder icon when there is none).
- Show a **Watched** marker when the film has been played (`playcount > 0`).
- Clicking a film card opens the same **video details modal** used on the
  Explorer view (see [video-explorer.md](video-explorer.md)), including Play and
  the ability to edit rating/tags/clip times. Metadata updates made in the modal
  are reflected in the search results.

## Keyboard

- Pressing `Escape` closes any open series popup or film details modal.
