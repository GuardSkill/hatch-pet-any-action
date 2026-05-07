# Animation Rows

`hatch-pet-any-action` uses a dynamic action list instead of one fixed 9-row atlas.

Defaults:

- 8 columns
- 192x208 pixels per cell
- row count equals the number of actions unless the manifest explicitly reserves more rows

Each package manifest should include:

```json
{
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

Rules:

- `idle` should exist unless the user explicitly rules it out.
- Rows are sequential by default.
- Unused cells after a row's final used column must be fully transparent.
- Frame counts may differ by action.
- More than 9 actions is valid as long as atlas rows expand to fit.
