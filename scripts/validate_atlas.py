#!/usr/bin/env python3
"""Validate a Codex pet spritesheet atlas."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from PIL import Image


def alpha_nonzero_count(image: Image.Image) -> int:
    alpha = image.getchannel("A")
    return sum(alpha.histogram()[1:])


def load_action_spec(spec_file: str) -> dict[str, object]:
    if not spec_file:
        raise SystemExit("--spec-file is required for hatch-pet-any-action atlas validation")

    raw = json.loads(Path(spec_file).expanduser().resolve().read_text(encoding="utf-8"))
    atlas = raw.get("atlas") if isinstance(raw.get("atlas"), dict) else {}
    actions = raw.get("actions")
    if not isinstance(actions, list) or not actions:
        raise SystemExit("spec file is missing actions")
    return {
        "actions": actions,
        "atlas": {
            "columns": int(atlas.get("columns") or 8),
            "rows": int(atlas.get("rows") or len(actions)),
        },
        "cell_width": int(raw.get("cell_width") or raw.get("cellWidth") or atlas.get("cell_width") or 192),
        "cell_height": int(raw.get("cell_height") or raw.get("cellHeight") or atlas.get("cell_height") or 208),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("atlas")
    parser.add_argument("--json-out")
    parser.add_argument("--spec-file", required=True)
    parser.add_argument("--min-used-pixels", type=int, default=50)
    parser.add_argument("--near-opaque-threshold", type=float, default=0.95)
    parser.add_argument("--allow-opaque", action="store_true")
    parser.add_argument("--allow-near-opaque-used-cells", action="store_true")
    args = parser.parse_args()

    atlas_path = Path(args.atlas).expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []
    near_opaque_used_cells: dict[str, list[int]] = defaultdict(list)
    cells: list[dict[str, object]] = []

    try:
        with Image.open(atlas_path) as opened:
            source_mode = opened.mode
            source_format = opened.format
            image = opened.convert("RGBA")
    except Exception as exc:  # noqa: BLE001
        result = {"ok": False, "errors": [f"could not open atlas: {exc}"], "warnings": []}
        print(json.dumps(result, indent=2))
        raise SystemExit(1)

    spec = load_action_spec(args.spec_file)
    columns = int(spec["atlas"]["columns"])
    rows = int(spec["atlas"]["rows"])
    cell_width = int(spec["cell_width"])
    cell_height = int(spec["cell_height"])
    atlas_width = columns * cell_width
    atlas_height = rows * cell_height

    if image.size != (atlas_width, atlas_height):
        errors.append(f"expected {atlas_width}x{atlas_height}, got {image.width}x{image.height}")

    if source_format not in {"PNG", "WEBP"}:
        errors.append(f"expected PNG or WebP, got {source_format}")

    if "A" not in source_mode and not args.allow_opaque:
        errors.append("atlas does not have an alpha channel")

    actions_by_row = {
        int(action["row"]): (str(action["id"]), int(action["frames"]))
        for action in spec["actions"]
    }
    for row_index in range(rows):
        state, frame_count = actions_by_row.get(row_index, (f"unused-row-{row_index}", 0))
        for column_index in range(columns):
            left = column_index * cell_width
            top = row_index * cell_height
            cell = image.crop((left, top, left + cell_width, top + cell_height))
            nontransparent = alpha_nonzero_count(cell)
            used = column_index < frame_count
            cell_info = {
                "state": state,
                "row": row_index,
                "column": column_index,
                "used": used,
                "nontransparent_pixels": nontransparent,
            }
            cells.append(cell_info)
            if used and nontransparent < args.min_used_pixels:
                errors.append(
                    f"{state} row {row_index} column {column_index} is empty or too sparse ({nontransparent} pixels)"
                )
            if used and nontransparent > cell_width * cell_height * args.near_opaque_threshold:
                near_opaque_used_cells[f"{state} row {row_index}"].append(column_index)
            if not used and nontransparent != 0:
                errors.append(
                    f"{state} row {row_index} unused column {column_index} is not transparent ({nontransparent} pixels)"
                )

    for row_label, columns in near_opaque_used_cells.items():
        message = (
            f"{row_label} has {len(columns)} nearly opaque used cells; "
            "this usually means the sprite has a non-transparent background"
        )
        if args.allow_near_opaque_used_cells:
            warnings.append(message)
        else:
            errors.append(message)

    alpha_count = alpha_nonzero_count(image)
    if alpha_count == atlas_width * atlas_height:
        message = "atlas is fully opaque; custom pets require a transparent sprite background"
        if args.allow_opaque:
            warnings.append(message)
        else:
            errors.append(message)

    result = {
        "ok": not errors,
        "file": str(atlas_path),
        "format": source_format,
        "mode": source_mode,
        "width": image.width,
        "height": image.height,
        "errors": errors,
        "warnings": warnings,
        "cells": cells,
    }

    if args.json_out:
        Path(args.json_out).expanduser().resolve().write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )

    print(json.dumps({k: v for k, v in result.items() if k != "cells"}, indent=2))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
