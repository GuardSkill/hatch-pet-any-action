# Hatch Pet Any Action Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a new `hatch-pet-any-action` skill that infers custom action sets and outputs compatible pet packages, then update the Pet Gallery viewer to render both new dynamic-action pets and legacy fixed-row pets.

**Architecture:** Copy the existing `hatch-pet` skill into a new sibling skill, move fixed row assumptions into run-time action metadata, and extend the viewer to read `pet.json.actions` when present while falling back to the legacy 9-action contract.

**Tech Stack:** Markdown skills, Python stdlib/Pillow scripts in the skill, HTML, CSS, vanilla JavaScript, existing local Pet Gallery backend

---

### Task 1: Inventory fixed-row assumptions

**Files:**
- Inspect: `/root/.codex/skills/hatch-pet/SKILL.md`
- Inspect: `/root/.codex/skills/hatch-pet/references/animation-rows.md`
- Inspect: `/root/.codex/skills/hatch-pet/scripts/prepare_pet_run.py`
- Inspect: `/root/.codex/skills/hatch-pet/scripts/compose_atlas.py`
- Inspect: `/root/.codex/skills/hatch-pet/scripts/validate_atlas.py`
- Inspect: `/root/.codex/skills/hatch-pet/scripts/render_animation_videos.py`
- Inspect: `/root/.codex/skills/hatch-pet/scripts/finalize_pet_run.py`
- Inspect: `/root/.codex/skills/hatch-pet/scripts/package_custom_pet.py`

**Step 1: Create a fixed-assumption checklist**

List every place that assumes:

- 9 states
- fixed row names
- fixed row indexes
- fixed atlas height
- fixed frame counts

**Step 2: Confirm the viewer assumptions**

Inspect:

- `script.js`
- `styles.css`

Document:

- hard-coded action definitions
- fixed background sizing
- any assumptions about exactly 9 rows

### Task 2: Clone the skill

**Files:**
- Create: `/root/.codex/skills/hatch-pet-any-action/`
- Copy: all relevant files from `/root/.codex/skills/hatch-pet/`

**Step 1: Copy the skill directory**

Preserve:

- `SKILL.md`
- `agents/openai.yaml`
- `references/`
- `scripts/`

**Step 2: Rename skill metadata**

Update:

- frontmatter name
- description
- any user-facing references to the old skill name where required

### Task 3: Add a dynamic action contract

**Files:**
- Modify: `/root/.codex/skills/hatch-pet-any-action/scripts/prepare_pet_run.py`
- Modify: `/root/.codex/skills/hatch-pet-any-action/references/animation-rows.md`
- Modify: `/root/.codex/skills/hatch-pet-any-action/SKILL.md`

**Step 1: Write failing tests or fixture checks**

If the skill has no test harness, create a minimal validation script or unit tests under the new skill scripts/tests area that assert:

- action inference emits an `actions` list
- action rows can be fewer than 9
- action rows can exceed 9

**Step 2: Implement action inference**

From natural language:

- infer a list of action specs
- normalize ids and labels
- assign frame counts
- assign row indexes
- ensure `idle` exists by default when appropriate

**Step 3: Persist action metadata**

Write the inferred action plan into the run manifest and any prompt/job manifests that downstream scripts consume.

### Task 4: Make generation scripts read dynamic actions

**Files:**
- Modify: `/root/.codex/skills/hatch-pet-any-action/scripts/prepare_pet_run.py`
- Modify: `/root/.codex/skills/hatch-pet-any-action/scripts/compose_atlas.py`
- Modify: `/root/.codex/skills/hatch-pet-any-action/scripts/validate_atlas.py`
- Modify: `/root/.codex/skills/hatch-pet-any-action/scripts/render_animation_videos.py`
- Modify: `/root/.codex/skills/hatch-pet-any-action/scripts/make_contact_sheet.py`
- Modify: `/root/.codex/skills/hatch-pet-any-action/scripts/queue_pet_repairs.py`
- Modify: `/root/.codex/skills/hatch-pet-any-action/scripts/finalize_pet_run.py`

**Step 1: Replace local row constants**

Every script should load the action list from the run manifest or a shared helper, not from hard-coded arrays.

**Step 2: Recompute atlas dimensions dynamically**

Support:

- fixed `columns = 8` default
- dynamic `rows = len(actions)`
- dynamic `height = rows * cell_height`

**Step 3: Update layout guides and QA**

Generate and validate guides based on each action's frame count and row index.

### Task 5: Package dynamic-action pets compatibly

**Files:**
- Modify: `/root/.codex/skills/hatch-pet-any-action/scripts/package_custom_pet.py`

**Step 1: Remove the fixed atlas-size gate**

Validate:

- cell dimensions
- format
- manifest completeness

Do not require `1536x1872` specifically.

**Step 2: Write extended `pet.json`**

Include:

- `cellWidth`
- `cellHeight`
- `atlas.columns`
- `atlas.rows`
- `actions`

Keep:

- `id`
- `displayName`
- `description`
- `spritesheetPath`

### Task 6: Update the Pet Gallery viewer

**Files:**
- Modify: `script.js`
- Modify: `tests/test_server.py` or add browser-logic-adjacent tests where reasonable

**Step 1: Add legacy fallback constants**

Keep the current 9-action list as `LEGACY_ACTIONS`.

**Step 2: Load manifest metadata**

When a pet is selected:

- fetch its manifest from `manifestUrl`
- use `manifest.actions` if present
- otherwise fall back to `LEGACY_ACTIONS`

**Step 3: Compute sheet geometry dynamically**

Use:

- `cellWidth`
- `cellHeight`
- `atlas.columns`
- `atlas.rows`
- maximum frame count across actions

Update:

- sprite sizing
- frame stepping
- animation grid rendering

**Step 4: Preserve old pets**

Verify bundled and previously uploaded legacy pets still render without manifest changes.

### Task 7: Update skill instructions and references

**Files:**
- Modify: `/root/.codex/skills/hatch-pet-any-action/SKILL.md`
- Modify: `/root/.codex/skills/hatch-pet-any-action/agents/openai.yaml`
- Modify: `/root/.codex/skills/hatch-pet-any-action/references/animation-rows.md`
- Modify: other reference docs if they mention hard-coded 9-row assumptions

**Step 1: Rewrite workflow language**

Document:

- action inference
- dynamic row counts
- compatibility manifest contract
- limits and heuristics

**Step 2: Keep the old skill untouched**

Ensure the new instructions do not overwrite the original `hatch-pet`.

### Task 8: Verify end to end

**Files:**
- No single file; verify outputs

**Step 1: Verify the new skill artifacts**

Run a dry or fixture-backed path that produces:

- a legacy-like action set
- a reduced action set
- an expanded action set

**Step 2: Verify viewer compatibility**

Confirm:

- old fixed-row pets render
- new dynamic-action pets render
- action buttons and animation grid match the manifest

**Step 3: Record residual risks**

If any script remains fixed-row, list it explicitly before calling the work complete.
