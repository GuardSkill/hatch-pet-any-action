# Hatch Pet Any Action Design

**Date:** 2026-05-07

## Goal

Create a new skill named `hatch-pet-any-action` by copying `hatch-pet` and extending it to infer custom action sets from natural-language descriptions. Keep output compatible with the existing pet package shape (`pet.json` + `spritesheet.webp`) while allowing fewer or more than nine actions, each with its own frame count. Update the Pet Gallery viewer so it can load these new packages while remaining backward-compatible with existing fixed-row pets.

## Current Constraints

The current `hatch-pet` stack is hard-wired to a fixed atlas contract:

- `SKILL.md` assumes one base job plus 9 row jobs.
- `references/animation-rows.md` defines the 9 fixed states.
- `scripts/prepare_pet_run.py` defines `ATLAS = 8x9` and a fixed `ROWS` array.
- `scripts/compose_atlas.py`, `validate_atlas.py`, and `render_animation_videos.py` assume the same row list and dimensions.
- `scripts/package_custom_pet.py` requires the atlas size `1536x1872`.
- The Pet Gallery frontend hard-codes the same 9 actions and fixed spritesheet background size.

This means the current pipeline cannot truthfully represent custom actions without changing both the skill output schema and the viewer.

## Recommended Approach

Keep the old skill intact and create a sibling skill:

- Source: `/root/.codex/skills/hatch-pet`
- New target: `/root/.codex/skills/hatch-pet-any-action`

This avoids destabilizing the original skill while allowing a new contract optimized for dynamic action sets.

## Compatibility Contract

Keep the package artifact names the same:

- `pet.json`
- `spritesheet.webp`

Extend `pet.json` with optional metadata. New packages include:

```json
{
  "id": "foxy",
  "displayName": "Foxy",
  "description": "Pixel fox Codex pet",
  "spritesheetPath": "spritesheet.webp",
  "cellWidth": 192,
  "cellHeight": 208,
  "atlas": {
    "columns": 8,
    "rows": 3
  },
  "actions": [
    { "id": "idle", "label": "Idle", "row": 0, "frames": 6 },
    { "id": "coding", "label": "Coding", "row": 1, "frames": 8 },
    { "id": "sleeping", "label": "Sleeping", "row": 2, "frames": 4 }
  ]
}
```

Backward compatibility rules:

- If `actions` metadata exists, the viewer must use it.
- If `actions` metadata is missing, the viewer falls back to the legacy 9-action defaults.
- `cellWidth` and `cellHeight` default to `192x208` when omitted.
- `atlas.columns` defaults to `8`.
- Legacy packs remain displayable without modification.

## Skill Behavior

`hatch-pet-any-action` should accept either:

- an explicit action list, or
- a natural-language description of the pet and its behaviors

When the user provides only natural language, the skill infers an action plan before image generation. The inferred plan should:

- include a calm baseline `idle` action unless the user explicitly asks otherwise
- choose actions that are visually distinct and readable at sprite scale
- avoid duplicate semantics
- default to a sane count range, recommended `4` to `16`
- keep per-action frame counts reasonable, recommended `2` to `12`

The inferred action plan becomes the single source of truth for:

- layout guides
- prompt generation
- row jobs
- atlas composition
- QA
- package manifest

## Data Model For Dynamic Actions

Each action entry should contain:

- `id`: stable slug for filenames and prompt ids
- `label`: user-facing display name
- `row`: atlas row index
- `frames`: frame count
- `purpose`: short description used in prompts and QA

The run manifest should carry the action plan so every downstream script consumes the same state list instead of a local constant.

## Skill Pipeline Changes

The new skill should reuse the existing overall pipeline shape:

1. Prepare run folder
2. Infer action plan
3. Generate base image
4. Generate row-strip jobs per action
5. Record selected outputs
6. Compose atlas
7. Run validation and QA
8. Package pet

But the following components must read dynamic action metadata instead of fixed constants:

- `prepare_pet_run.py`
- `compose_atlas.py`
- `validate_atlas.py`
- `render_animation_videos.py`
- `make_contact_sheet.py`
- `queue_pet_repairs.py`
- `finalize_pet_run.py`
- `package_custom_pet.py`
- any docs and status scripts that surface row information

## Viewer Changes

The Pet Gallery viewer must stop hard-coding the action list.

New viewer rules:

- fetch `pet.json` when needed for the selected pet
- use `manifest.actions` when present
- otherwise use the current legacy default action table
- compute background size from `atlas.columns`, `atlas.rows`, `cellWidth`, and `cellHeight`
- render the action buttons and animation grid dynamically

This keeps existing pets working while enabling new multi-action pets immediately.

## Action Inference Strategy

Recommended action inference order:

1. Normalize the user request into short candidate behaviors
2. Keep only sprite-readable, loop-friendly actions
3. Insert `idle` if absent and appropriate
4. Assign practical frame counts
5. Assign sequential row indexes
6. Persist the inferred plan into the run manifest

Suggested default heuristics:

- `idle`: 4-6 frames
- low-motion loops: 4-6 frames
- directional or busy loops: 6-8 frames
- expressive beats: 3-5 frames
- cap at 12 unless explicitly requested

## Risks

The main risks are:

- prompt drift when inferred custom actions are too abstract
- QA scripts missing one of the fixed-row assumptions
- atlas size growth increasing package size and viewer cost
- old pets breaking if the viewer loses its fallback path

## Testing Strategy

Tests should cover both sides:

- dynamic manifest generation for the new skill
- legacy package compatibility in the viewer
- action metadata parsing
- atlas composition and validation with non-9-row sets
- frame-count variation across actions
- old fixed-row pets still rendering correctly

## Recommendation

Implement the new skill as a clean copy with shared concepts but separate files. Do not retrofit the original `hatch-pet` in place. On the viewer side, keep the old defaults as a compatibility fallback and make `pet.json.actions` the new preferred contract.
