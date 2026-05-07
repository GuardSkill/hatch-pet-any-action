# Codex Pet Contract

## Sprite Atlas

- Format: PNG or WebP.
- Dimensions: `atlas.columns * cellWidth` by `atlas.rows * cellHeight`.
- Grid: default 8 columns, dynamic rows.
- Cell: default `192x208`.
- Background: transparent.
- Unused cells: fully transparent.

The webview animation uses CSS background positions from `pet.json` action metadata. Do not add labels, gutters, borders, grid lines, shadows outside the cell, or extra frames.

## Local Custom Pet Package

Place files under:

```text
${CODEX_HOME:-$HOME/.codex}/pets/<pet-name>/
├── pet.json
└── spritesheet.webp
```

Manifest shape:

```json
{
  "id": "pet-name",
  "displayName": "Pet Name",
  "description": "One short sentence.",
  "spritesheetPath": "spritesheet.webp",
  "cellWidth": 192,
  "cellHeight": 208,
  "atlas": { "columns": 8, "rows": 3 },
  "actions": [
    { "id": "idle", "label": "Idle", "row": 0, "frames": 6 },
    { "id": "coding", "label": "Coding", "row": 1, "frames": 8 },
    { "id": "sleeping", "label": "Sleeping", "row": 2, "frames": 4 }
  ]
}
```

The app loads custom pets from the folder name under `${CODEX_HOME:-$HOME/.codex}/pets/`.
