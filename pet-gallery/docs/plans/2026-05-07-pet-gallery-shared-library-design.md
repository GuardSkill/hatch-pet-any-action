# Pet Gallery Shared Library Design

**Date:** 2026-05-07

## Goal

Turn the current single-browser pet preview page into a shared library that persists pets on disk, works across browsers, allows downloading existing pet packages, and requires password `104228` for deletion. The local service and FRP tunnel must both be started from the interactive `~/.zshrc` flow.

## Current State

The project is a static HTML/CSS/JS page. Uploaded pets are stored in `localStorage`, so they are isolated per browser profile and disappear outside the current browser context. There is no backend, no server-side persistence, no secure delete flow, and no package download endpoint.

## Recommended Architecture

Use a single lightweight Python service with no external dependencies.

- Serve the static frontend from the project directory.
- Expose JSON API endpoints for listing, uploading, and deleting pets.
- Persist uploaded pet packages under a local `data/pets/` directory.
- Generate downloadable ZIP archives in memory with Python `zipfile`.
- Keep bundled pets available from the repo `assets/` directory and expose them through the same API shape as uploaded pets.

## Data Model

Each pet record returned to the frontend will include:

- `id`
- `displayName`
- `description`
- `source` as `bundled` or `uploaded`
- `spritesheetUrl`
- `manifestUrl`
- `downloadUrl`
- `canDelete`

Uploaded pets are stored as:

- `data/pets/index.json`
- `data/pets/<pet-id>/pet.json`
- `data/pets/<pet-id>/spritesheet.webp` or `.png`

Bundled pets are resolved from a small server-side catalog and point to checked-in assets.

## API Surface

- `GET /api/pets`
  Returns the full merged library of bundled and uploaded pets.

- `POST /api/pets`
  Accepts JSON with manifest metadata plus base64-encoded spritesheet content.
  Validates required fields, normalizes the pet id, and stores the package on disk.

- `DELETE /api/pets/<id>`
  Requires JSON body with `password`.
  Only uploaded pets may be deleted. Password must equal `104228`.

- `GET /api/pets/<id>/download`
  Streams a ZIP archive containing `pet.json` and the spritesheet.

## Frontend Changes

Replace localStorage-backed uploads with API-backed state.

- Load pets from `/api/pets` on startup.
- Keep the bundled pets visible, but sourced from the API.
- Add per-pet actions in the library list:
  - `Preview`
  - `Download`
  - `Delete` for uploaded pets only
- Add an overwrite confirmation when uploading a pet whose id already exists.
- Add a password modal for deletion with clear success and failure feedback.
- Keep the existing animation preview and prompt builder intact.

## UX Direction

The current page is functional but sparse. The update should keep the existing visual language while making the library panel feel intentional:

- Pet cards instead of plain rows.
- Inline metadata badges for source and delete availability.
- Action buttons grouped on each card.
- Upload area with clear “shared library” messaging.
- A lightweight modal for delete confirmation and password entry.
- A status banner for upload, delete, and download errors.

## Autostart

`/usr/local/bin/pet-gallery-autostart.sh` will manage:

- the Python service on `127.0.0.1:13645`
- `frpc -c /usr/local/frp_0.55.1_linux_amd64/pet_gallery.toml`

The script must:

- detect whether the service process is already running
- detect whether the target port is already occupied
- detect whether the exact FRP config is already running
- start missing processes in the background with log files

`~/.zshrc` should call this script only inside the existing interactive-shell branch.

## Error Handling

- Invalid manifest or missing spritesheet blocks upload with a clear error.
- Deleting bundled pets returns a friendly “not allowed” message.
- Wrong delete password returns `403`.
- Conflicting upload ids trigger explicit overwrite confirmation before POST.
- If the service port is occupied by another process, the autostart script logs and skips starting a second instance.

## Testing Strategy

Test the Python store and API behavior first with `unittest`.

- list pets merges bundled and uploaded records
- upload persists files and metadata
- overwrite replaces an existing uploaded pet
- delete requires the correct password
- download returns a ZIP containing both files

Frontend verification will be manual in browser because this project currently has no browser test harness.
