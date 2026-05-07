#!/usr/bin/env python3
"""Package a validated atlas as a local Codex pet."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from pathlib import Path

from PIL import Image


def default_codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or "~/.codex").expanduser().resolve()


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip("-")


def validate_spritesheet(
    path: Path,
    *,
    cell_width: int,
    cell_height: int,
    atlas_columns: int,
    atlas_rows: int,
) -> str:
    with Image.open(path) as image:
        expected_size = (atlas_columns * cell_width, atlas_rows * cell_height)
        if image.size != expected_size:
            raise SystemExit(
                f"expected {expected_size[0]}x{expected_size[1]}, got {image.width}x{image.height}"
            )
        if image.format not in {"PNG", "WEBP"}:
            raise SystemExit(f"expected PNG or WebP, got {image.format}")
        return str(image.format)


def write_webp_spritesheet(source: Path, target: Path, source_format: str) -> None:
    if source_format == "WEBP":
        shutil.copy2(source, target)
        return
    with Image.open(source) as image:
        target.parent.mkdir(parents=True, exist_ok=True)
        image.convert("RGBA").save(
            target,
            format="WEBP",
            lossless=True,
            quality=100,
            method=6,
        )


def positive_int(value: str, field: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise SystemExit(f"{field} must be an integer") from error
    if parsed <= 0:
        raise SystemExit(f"{field} must be positive")
    return parsed


def load_actions(
    *,
    actions_json: str,
    actions_file: str,
    spec_file: str,
) -> list[dict[str, object]]:
    if actions_json:
        raw = json.loads(actions_json)
        if not isinstance(raw, list):
            raise SystemExit("--actions-json must be a JSON array")
        return raw
    if actions_file:
        raw = json.loads(Path(actions_file).expanduser().resolve().read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise SystemExit("--actions-file must contain a JSON array")
        return raw
    if spec_file:
        raw = json.loads(Path(spec_file).expanduser().resolve().read_text(encoding="utf-8"))
        actions = raw.get("actions")
        if not isinstance(actions, list):
            raise SystemExit("--spec-file is missing actions")
        return actions
    return []


def load_geometry_defaults(spec_file: str) -> dict[str, int]:
    if not spec_file:
        return {
            "cell_width": 192,
            "cell_height": 208,
            "atlas_columns": 8,
            "atlas_rows": 0,
        }
    raw = json.loads(Path(spec_file).expanduser().resolve().read_text(encoding="utf-8"))
    atlas = raw.get("atlas") if isinstance(raw.get("atlas"), dict) else {}
    return {
        "cell_width": int(raw.get("cell_width") or raw.get("cellWidth") or atlas.get("cell_width") or atlas.get("cellWidth") or 192),
        "cell_height": int(raw.get("cell_height") or raw.get("cellHeight") or atlas.get("cell_height") or atlas.get("cellHeight") or 208),
        "atlas_columns": int(atlas.get("columns") or 8),
        "atlas_rows": int(atlas.get("rows") or max(len(raw.get("actions") or []), 1)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pet-name", default="")
    parser.add_argument("--display-name", default="")
    parser.add_argument("--description", required=True)
    parser.add_argument("--spritesheet", required=True)
    parser.add_argument("--cell-width", default="")
    parser.add_argument("--cell-height", default="")
    parser.add_argument("--atlas-columns", default="")
    parser.add_argument("--atlas-rows", default="")
    parser.add_argument("--actions-json", default="")
    parser.add_argument("--actions-file", default="")
    parser.add_argument("--spec-file", default="")
    parser.add_argument("--codex-home", default=str(default_codex_home()))
    parser.add_argument(
        "--output-dir",
        help="Exact pet package directory. Defaults to ${CODEX_HOME:-$HOME/.codex}/pets/<pet-name>.",
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    raw_pet_name = (args.pet_name or args.display_name).strip()
    if not raw_pet_name:
        raise SystemExit("pet name is required")
    pet_id = slugify(raw_pet_name)
    if not pet_id:
        raise SystemExit("pet name must contain at least one letter or digit")
    display_name = (args.display_name or raw_pet_name).strip()

    source = Path(args.spritesheet).expanduser().resolve()
    actions = load_actions(
        actions_json=args.actions_json,
        actions_file=args.actions_file,
        spec_file=args.spec_file,
    )
    geometry_defaults = load_geometry_defaults(args.spec_file)
    cell_width = positive_int(args.cell_width, "cell width") if args.cell_width else geometry_defaults["cell_width"]
    cell_height = positive_int(args.cell_height, "cell height") if args.cell_height else geometry_defaults["cell_height"]
    implied_rows = max((int(action.get("row", index)) for index, action in enumerate(actions)), default=0) + 1
    implied_columns = max((int(action.get("frames", 1)) for action in actions), default=8)
    atlas_columns = (
        positive_int(args.atlas_columns, "atlas columns")
        if args.atlas_columns
        else max(geometry_defaults["atlas_columns"], implied_columns)
    )
    atlas_rows = (
        positive_int(args.atlas_rows, "atlas rows")
        if args.atlas_rows
        else max(geometry_defaults["atlas_rows"], implied_rows, 1)
    )
    source_format = validate_spritesheet(
        source,
        cell_width=cell_width,
        cell_height=cell_height,
        atlas_columns=atlas_columns,
        atlas_rows=atlas_rows,
    )
    target_dir = (
        Path(args.output_dir).expanduser().resolve()
        if args.output_dir
        else Path(args.codex_home).expanduser().resolve() / "pets" / pet_id
    )
    target_dir.mkdir(parents=True, exist_ok=True)

    target_sheet = target_dir / "spritesheet.webp"
    manifest_path = target_dir / "pet.json"
    if not args.force and (target_sheet.exists() or manifest_path.exists()):
        raise SystemExit(f"{target_dir} already contains pet files; pass --force to overwrite")

    write_webp_spritesheet(source, target_sheet, source_format)
    manifest = {
        "id": pet_id,
        "displayName": display_name,
        "description": args.description,
        "spritesheetPath": target_sheet.name,
        "cellWidth": cell_width,
        "cellHeight": cell_height,
        "atlas": {
            "columns": atlas_columns,
            "rows": atlas_rows,
        },
        "actions": actions,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {"ok": True, "pet_dir": str(target_dir), "manifest": str(manifest_path)}, indent=2
        )
    )


if __name__ == "__main__":
    main()
