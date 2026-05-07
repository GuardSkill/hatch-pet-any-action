# Pet Gallery Shared Library Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a shared persistent pet library with upload, download, and password-protected delete, backed by a local Python service that autostarts with FRP from interactive `~/.zshrc`.

**Architecture:** A standard-library Python HTTP server owns persistence and API routes while also serving the existing static frontend. Uploaded pet packages are stored on disk under `data/pets`, bundled pets are exposed through a small catalog, and the frontend switches from `localStorage` to the API.

**Tech Stack:** HTML, CSS, vanilla JavaScript, Python 3 stdlib (`http.server`, `json`, `zipfile`, `base64`, `unittest`)

---

### Task 1: Backend tests

**Files:**
- Create: `tests/test_server.py`

**Step 1: Write failing tests**

Cover:

- listing bundled pets
- persisting an uploaded pet
- overwriting an uploaded pet
- rejecting delete with wrong password
- deleting uploaded pet with correct password
- downloading a ZIP package

**Step 2: Run tests to verify failure**

Run: `python3 -m unittest discover -s tests -v`
Expected: FAIL because `server.py` does not exist yet.

### Task 2: Backend service

**Files:**
- Create: `server.py`
- Create: `data/.gitkeep`

**Step 1: Implement storage helpers**

- create and load `data/pets/index.json`
- normalize manifest and ids
- read bundled catalog
- persist uploaded manifests and spritesheets
- delete uploaded pets
- build downloadable ZIP archives in memory

**Step 2: Implement API and static serving**

- `GET /api/pets`
- `POST /api/pets`
- `DELETE /api/pets/<id>`
- `GET /api/pets/<id>/download`
- static file serving for `/`, `/assets/*`, `/styles.css`, `/script.js`, `/data/pets/*`

**Step 3: Run tests**

Run: `python3 -m unittest discover -s tests -v`
Expected: PASS

### Task 3: Frontend integration

**Files:**
- Modify: `index.html`
- Modify: `script.js`
- Modify: `styles.css`

**Step 1: Replace local state model**

- fetch pets from API on load
- upload via JSON POST instead of `localStorage`
- remove browser-local persistence behavior

**Step 2: Add new UI and interactions**

- status banner
- pet cards with source badge and actions
- overwrite confirmation flow
- delete password modal
- download action

**Step 3: Manual verification**

- load page
- upload pet
- refresh in another browser
- download package
- delete with wrong and correct password

### Task 4: Autostart integration

**Files:**
- Modify: `/usr/local/bin/pet-gallery-autostart.sh`
- Modify: `/root/.zshrc`

**Step 1: Update the autostart script**

- ensure `server.py` is running on port `13645`
- ensure the exact FRP config is running
- log to `/var/log/pet-gallery-server.log` and `/var/log/pet-gallery-frpc.log`

**Step 2: Update interactive shell startup**

- call `/usr/local/bin/pet-gallery-autostart.sh` in the interactive branch

**Step 3: Verify**

- run the script manually
- confirm the Python service and FRP process are running once

### Task 5: Final verification

**Files:**
- No new files

**Step 1: Verify backend tests**

Run: `python3 -m unittest discover -s tests -v`

**Step 2: Verify service health**

Run: `curl -s http://127.0.0.1:13645/api/pets`

**Step 3: Verify autostart idempotency**

Run the autostart script twice and confirm it does not spawn duplicates.
