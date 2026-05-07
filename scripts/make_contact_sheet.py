#!/usr/bin/env python3
"""Create a labeled contact sheet from a Codex pet atlas."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

LABEL_HEIGHT = 22


def checker(size: tuple[int, int], square: int = 16) -> Image.Image:
    image = Image.new("RGB", size, "#ffffff")
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], square):
        for x in range(0, size[0], square):
            if (x // square + y // square) % 2:
                draw.rectangle((x, y, x + square - 1, y + square - 1), fill="#e8e8e8")
    return image


def load_action_spec(spec_file: str) -> tuple[list[dict[str, object]], int, int, int]:
    if not spec_file:
        raise SystemExit("--spec-file is required for hatch-pet-any-action contact sheets")

    raw = json.loads(Path(spec_file).expanduser().resolve().read_text(encoding="utf-8"))
    actions = raw.get("actions")
    atlas = raw.get("atlas") if isinstance(raw.get("atlas"), dict) else {}
    if not isinstance(actions, list) or not actions:
        raise SystemExit("spec file is missing actions")
    columns = int(atlas.get("columns") or 8)
    cell_width = int(raw.get("cell_width") or raw.get("cellWidth") or atlas.get("cell_width") or 192)
    cell_height = int(raw.get("cell_height") or raw.get("cellHeight") or atlas.get("cell_height") or 208)
    return actions, columns, cell_width, cell_height


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("atlas")
    parser.add_argument("--output", required=True)
    parser.add_argument("--spec-file", required=True)
    parser.add_argument("--scale", type=float, default=0.5)
    args = parser.parse_args()

    with Image.open(Path(args.atlas).expanduser().resolve()) as opened:
        atlas = opened.convert("RGBA")

    actions, columns, source_cell_width, source_cell_height = load_action_spec(args.spec_file)
    cell_w = max(1, round(source_cell_width * args.scale))
    cell_h = max(1, round(source_cell_height * args.scale))
    rows = max(int(action["row"]) for action in actions) + 1
    width = columns * cell_w
    height = rows * (cell_h + LABEL_HEIGHT)
    sheet = Image.new("RGB", (width, height), "#f7f7f7")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    actions_by_row = {int(action["row"]): action for action in actions}

    for row in range(rows):
        action = actions_by_row.get(row, {"id": f"unused-row-{row}", "label": f"Unused {row}", "frames": 0})
        y = row * (cell_h + LABEL_HEIGHT)
        draw.rectangle((0, y, width, y + LABEL_HEIGHT - 1), fill="#111111")
        draw.text((6, y + 5), f"row {row}: {action.get('label') or action['id']}", fill="#ffffff", font=font)
        draw.text(
            (width - 92, y + 5),
            f"{int(action['frames'])} frames",
            fill="#ffffff",
            font=font,
        )
        for column in range(columns):
            crop = atlas.crop(
                (
                    column * source_cell_width,
                    row * source_cell_height,
                    (column + 1) * source_cell_width,
                    (row + 1) * source_cell_height,
                )
            )
            crop = crop.resize((cell_w, cell_h), Image.Resampling.LANCZOS)
            bg = checker((cell_w, cell_h))
            bg.paste(crop, (0, 0), crop)
            x = column * cell_w
            sheet.paste(bg, (x, y + LABEL_HEIGHT))
            outline = "#18a058" if column < int(action["frames"]) else "#cc3344"
            draw.rectangle(
                (x, y + LABEL_HEIGHT, x + cell_w - 1, y + LABEL_HEIGHT + cell_h - 1),
                outline=outline,
            )
            draw.text((x + 4, y + LABEL_HEIGHT + 4), str(column), fill="#111111", font=font)

    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
