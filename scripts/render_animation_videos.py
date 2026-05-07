#!/usr/bin/env python3
"""Render Codex pet state videos from an atlas using ffmpeg."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw


def checker(size: tuple[int, int], square: int = 16) -> Image.Image:
    image = Image.new("RGB", size, "#ffffff")
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], square):
        for x in range(0, size[0], square):
            if (x // square + y // square) % 2:
                draw.rectangle((x, y, x + square - 1, y + square - 1), fill="#e8e8e8")
    return image


def shell_quote_for_concat(path: Path) -> str:
    return "'" + str(path).replace("'", "'\\''") + "'"


def load_action_spec(spec_file: str) -> tuple[list[dict[str, object]], int, int]:
    if not spec_file:
        raise SystemExit("--spec-file is required for hatch-pet-any-action preview videos")

    raw = json.loads(Path(spec_file).expanduser().resolve().read_text(encoding="utf-8"))
    actions = raw.get("actions")
    if not isinstance(actions, list) or not actions:
        raise SystemExit("spec file is missing actions")
    atlas = raw.get("atlas") if isinstance(raw.get("atlas"), dict) else {}
    cell_width = int(raw.get("cell_width") or raw.get("cellWidth") or atlas.get("cell_width") or 192)
    cell_height = int(raw.get("cell_height") or raw.get("cellHeight") or atlas.get("cell_height") or 208)
    return actions, cell_width, cell_height


def render_state(
    atlas: Image.Image,
    state: str,
    row: int,
    durations: list[int],
    output_dir: Path,
    loops: int,
    scale: int,
    ffmpeg: str,
    *,
    cell_width: int,
    cell_height: int,
) -> None:
    with tempfile.TemporaryDirectory(prefix=f"codex-pet-{state}-") as temp_raw:
        temp = Path(temp_raw)
        frame_paths: list[Path] = []
        for column in range(len(durations)):
            crop = atlas.crop(
                (
                    column * cell_width,
                    row * cell_height,
                    (column + 1) * cell_width,
                    (row + 1) * cell_height,
                )
            ).convert("RGBA")
            bg = checker((cell_width, cell_height))
            bg.paste(crop, (0, 0), crop)
            frame_path = temp / f"{state}-{column:02d}.png"
            bg.save(frame_path)
            frame_paths.append(frame_path)

        concat_path = temp / f"{state}.ffconcat"
        lines = ["ffconcat version 1.0"]
        sequence: list[tuple[Path, int]] = []
        for _ in range(loops):
            sequence.extend(zip(frame_paths, durations, strict=True))
        for frame_path, duration_ms in sequence:
            lines.append(f"file {shell_quote_for_concat(frame_path)}")
            lines.append(f"duration {duration_ms / 1000:.3f}")
        lines.append(f"file {shell_quote_for_concat(sequence[-1][0])}")
        concat_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        output = output_dir / f"{state}.mp4"
        command = [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_path),
            "-vf",
            f"scale={cell_width * scale}:{cell_height * scale}:flags=lanczos,format=yuv420p",
            "-movflags",
            "+faststart",
            str(output),
        ]
        subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("atlas")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--spec-file", required=True)
    parser.add_argument("--loops", type=int, default=4)
    parser.add_argument("--scale", type=int, default=2)
    parser.add_argument("--ffmpeg", default=shutil.which("ffmpeg") or "ffmpeg")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    with Image.open(Path(args.atlas).expanduser().resolve()) as opened:
        atlas = opened.convert("RGBA")

    actions, cell_width, cell_height = load_action_spec(args.spec_file)

    for action in actions:
        render_state(
            atlas,
            str(action["id"]),
            int(action["row"]),
            [int(value) for value in action.get("durations", [])] or [140] * int(action["frames"]),
            output_dir,
            args.loops,
            args.scale,
            args.ffmpeg,
            cell_width=cell_width,
            cell_height=cell_height,
        )
    print(f"wrote videos to {output_dir}")


if __name__ == "__main__":
    main()
