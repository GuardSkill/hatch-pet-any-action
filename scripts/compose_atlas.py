#!/usr/bin/env python3
"""Compose or normalize a Codex pet spritesheet atlas."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

IMAGE_SUFFIXES = {".png", ".webp", ".jpg", ".jpeg"}


def image_files(path: Path) -> list[Path]:
    return sorted(p for p in path.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES)


def find_row_frames(root: Path, state: str, row_index: int) -> list[Path]:
    candidates = [
        root / state,
        root / f"row-{row_index}",
        root / f"row{row_index}",
        root / f"{row_index}-{state}",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            files = image_files(candidate)
            if files:
                return files
    globs = [
        f"{state}_*",
        f"{state}-*",
        f"row{row_index}_*",
        f"row-{row_index}-*",
    ]
    files: list[Path] = []
    for pattern in globs:
        files.extend(p for p in root.glob(pattern) if p.suffix.lower() in IMAGE_SUFFIXES)
    return sorted(set(files))


def load_action_spec(frames_root: Path | None, spec_file: Path | None) -> dict[str, object]:
    candidate = spec_file
    if candidate is None and frames_root is not None:
        candidate = frames_root / "frames-manifest.json"
    if candidate is None or not candidate.is_file():
        raise SystemExit("missing action spec; pass --spec-file or use --frames-root with frames-manifest.json")
    manifest = json.loads(candidate.read_text(encoding="utf-8"))
    atlas = manifest.get("atlas")
    actions = manifest.get("actions")
    if not isinstance(atlas, dict) or not isinstance(actions, list):
        raise SystemExit("action spec is missing atlas/actions metadata")
    cell_width = int(manifest.get("cell_width") or atlas.get("cell_width") or 192)
    cell_height = int(manifest.get("cell_height") or atlas.get("cell_height") or 208)
    return {
        "atlas": {
            "columns": int(atlas.get("columns") or 8),
            "rows": int(atlas.get("rows") or len(actions)),
        },
        "actions": actions,
        "cell_width": cell_width,
        "cell_height": cell_height,
    }


def paste_centered(
    atlas: Image.Image,
    source: Image.Image,
    row: int,
    column: int,
    *,
    cell_width: int,
    cell_height: int,
) -> None:
    frame = source.convert("RGBA")
    if frame.size != (cell_width, cell_height):
        frame.thumbnail((cell_width, cell_height), Image.Resampling.LANCZOS)
    left = column * cell_width + (cell_width - frame.width) // 2
    top = row * cell_height + (cell_height - frame.height) // 2
    atlas.alpha_composite(frame, (left, top))


def compose_from_source_atlas(path: Path, resize_source: bool, spec: dict[str, object]) -> Image.Image:
    columns = int(spec["atlas"]["columns"])
    rows = int(spec["atlas"]["rows"])
    cell_width = int(spec["cell_width"])
    cell_height = int(spec["cell_height"])
    atlas_width = columns * cell_width
    atlas_height = rows * cell_height
    atlas_aspect_ratio = atlas_width / atlas_height
    with Image.open(path) as opened:
        source = opened.convert("RGBA")
    if source.size != (atlas_width, atlas_height):
        if not resize_source:
            raise SystemExit(
                f"source atlas must be {atlas_width}x{atlas_height}; got {source.width}x{source.height}"
            )
        source_ratio = source.width / source.height
        if abs(source_ratio - atlas_aspect_ratio) > 0.02:
            raise SystemExit(
                "refusing to resize source atlas because its aspect ratio does not match "
                f"the requested atlas ratio {atlas_aspect_ratio:.3f}; got {source_ratio:.3f}. "
                "Generate exact atlas dimensions or use --frames-root."
            )
        source = source.resize((atlas_width, atlas_height), Image.Resampling.LANCZOS)

    atlas = Image.new("RGBA", (atlas_width, atlas_height), (0, 0, 0, 0))
    for action in spec["actions"]:
        row = int(action["row"])
        frame_count = int(action["frames"])
        for column in range(frame_count):
            left = column * cell_width
            top = row * cell_height
            cell = source.crop((left, top, left + cell_width, top + cell_height))
            atlas.alpha_composite(cell, (left, top))
    return atlas


def compose_from_frames(root: Path, spec: dict[str, object]) -> Image.Image:
    columns = int(spec["atlas"]["columns"])
    rows = int(spec["atlas"]["rows"])
    cell_width = int(spec["cell_width"])
    cell_height = int(spec["cell_height"])
    atlas = Image.new("RGBA", (columns * cell_width, rows * cell_height), (0, 0, 0, 0))
    for action in spec["actions"]:
        state = str(action["id"])
        row = int(action["row"])
        frame_count = int(action["frames"])
        files = find_row_frames(root, state, row)
        if len(files) < frame_count:
            raise SystemExit(
                f"{state} row needs {frame_count} frames, found {len(files)} under {root}"
            )
        for column, frame_path in enumerate(files[:frame_count]):
            with Image.open(frame_path) as frame:
                paste_centered(
                    atlas,
                    frame,
                    row,
                    column,
                    cell_width=cell_width,
                    cell_height=cell_height,
                )
    return atlas


def save_outputs(atlas: Image.Image, output: Path, webp_output: Path | None) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(output)
    if webp_output is not None:
        webp_output.parent.mkdir(parents=True, exist_ok=True)
        atlas.save(webp_output, format="WEBP", lossless=True, quality=100, method=6)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--source-atlas")
    source.add_argument("--frames-root")
    parser.add_argument("--output", required=True)
    parser.add_argument("--webp-output")
    parser.add_argument(
        "--spec-file",
        help="Path to pet_request.json or frames-manifest.json with atlas/action metadata.",
    )
    parser.add_argument(
        "--resize-source",
        action="store_true",
        help="Resize a lower-resolution source atlas only when it already has the Codex atlas aspect ratio.",
    )
    args = parser.parse_args()
    frames_root = Path(args.frames_root).expanduser().resolve() if args.frames_root else None
    spec = load_action_spec(
        frames_root,
        Path(args.spec_file).expanduser().resolve() if args.spec_file else None,
    )

    if args.source_atlas:
        atlas = compose_from_source_atlas(
            Path(args.source_atlas).expanduser().resolve(),
            args.resize_source,
            spec,
        )
    else:
        atlas = compose_from_frames(frames_root, spec)

    save_outputs(
        atlas,
        Path(args.output).expanduser().resolve(),
        Path(args.webp_output).expanduser().resolve() if args.webp_output else None,
    )
    print(f"wrote {Path(args.output).expanduser().resolve()}")
    if args.webp_output:
        print(f"wrote {Path(args.webp_output).expanduser().resolve()}")


if __name__ == "__main__":
    main()
