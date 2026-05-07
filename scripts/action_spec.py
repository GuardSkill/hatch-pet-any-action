#!/usr/bin/env python3
"""Shared helpers for dynamic hatch-pet action manifests."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Mapping

DEFAULT_CELL_WIDTH = 192
DEFAULT_CELL_HEIGHT = 208
DEFAULT_COLUMNS = 8
DEFAULT_DURATION_MS = 140
DEFAULT_FINAL_DURATION_MS = 220

_DEFAULT_ACTIONS = [
    {
        "id": "idle",
        "label": "Idle",
        "frames": 6,
        "purpose": "neutral breathing/blinking loop",
        "durations": [280, 110, 110, 140, 140, 320],
        "keywords": ["idle", "resting", "calm", "baseline", "neutral", "still"],
    },
    {
        "id": "running-right",
        "label": "Running Right",
        "frames": 8,
        "purpose": "rightward locomotion loop",
        "durations": [120, 120, 120, 120, 120, 120, 120, 220],
        "keywords": ["running right", "move right", "rightward"],
    },
    {
        "id": "running-left",
        "label": "Running Left",
        "frames": 8,
        "purpose": "leftward locomotion loop",
        "durations": [120, 120, 120, 120, 120, 120, 120, 220],
        "keywords": ["running left", "move left", "leftward"],
    },
    {
        "id": "waving",
        "label": "Waving",
        "frames": 4,
        "purpose": "greeting gesture with raised wave and return",
        "durations": [140, 140, 140, 280],
        "keywords": ["wave", "waving", "hello", "greet", "greeting"],
    },
    {
        "id": "jumping",
        "label": "Jumping",
        "frames": 5,
        "purpose": "anticipation, lift, peak, descent, settle",
        "durations": [140, 140, 140, 140, 280],
        "keywords": ["jump", "jumping", "hop", "bounce", "leap"],
    },
    {
        "id": "failed",
        "label": "Failed",
        "frames": 8,
        "purpose": "sad, failed, or deflated reaction",
        "durations": [140, 140, 140, 140, 140, 140, 140, 240],
        "keywords": ["failed", "error", "sad", "deflated", "broken", "crash"],
    },
    {
        "id": "waiting",
        "label": "Waiting",
        "frames": 6,
        "purpose": "patient waiting loop with small motion",
        "durations": [150, 150, 150, 150, 150, 260],
        "keywords": ["wait", "waiting", "patient", "pause", "stand by"],
    },
    {
        "id": "running",
        "label": "Running",
        "frames": 6,
        "purpose": "active working or in-progress loop",
        "durations": [120, 120, 120, 120, 120, 220],
        "keywords": ["busy", "working", "processing", "task", "run", "running"],
    },
    {
        "id": "review",
        "label": "Review",
        "frames": 6,
        "purpose": "focused inspecting or review loop",
        "durations": [150, 150, 150, 150, 150, 280],
        "keywords": ["review", "inspect", "checking", "looking", "analyze"],
    },
    {
        "id": "coding",
        "label": "Coding",
        "frames": 6,
        "purpose": "busy coding or typing loop",
        "durations": [130, 130, 130, 130, 130, 240],
        "keywords": ["code", "coding", "typing", "programming", "debugging", "hack"],
    },
    {
        "id": "sleeping",
        "label": "Sleeping",
        "frames": 6,
        "purpose": "sleeping or resting loop",
        "durations": [220, 180, 180, 220, 220, 320],
        "keywords": ["sleep", "sleeping", "nap", "napping", "doze", "rest"],
    },
    {
        "id": "celebrating",
        "label": "Celebrating",
        "frames": 6,
        "purpose": "celebration loop with clear upbeat motion",
        "durations": [120, 120, 120, 120, 120, 240],
        "keywords": ["celebrate", "celebrating", "cheer", "victory", "party"],
    },
    {
        "id": "spinning",
        "label": "Spinning",
        "frames": 6,
        "purpose": "spin or twirl loop",
        "durations": [120, 120, 120, 120, 120, 240],
        "keywords": ["spin", "spinning", "twirl", "pirouette", "rotate"],
    },
]

DEFAULT_ACTIONS_BY_ID = {action["id"]: action for action in _DEFAULT_ACTIONS}


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip("-")


def display_from_slug(value: str) -> str:
    words = [word for word in re.split(r"[^a-zA-Z0-9]+", value.strip()) if word]
    return " ".join(word.capitalize() for word in words)


def _as_int(value: object, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _read_mapping_int(mapping: Mapping[str, object], *keys: str, default: int) -> int:
    for key in keys:
        if key in mapping:
            return _as_int(mapping[key], default)
    return default


def _normalize_durations(raw: object, frame_count: int, fallback: object = None) -> list[int]:
    durations: list[int] = []
    for source in (raw, fallback):
        if isinstance(source, list):
            durations = [_as_int(value, DEFAULT_DURATION_MS) for value in source]
            if durations:
                break
    if not durations:
        durations = [DEFAULT_DURATION_MS] * frame_count
        durations[-1] = DEFAULT_FINAL_DURATION_MS
        return durations
    if len(durations) < frame_count:
        durations.extend([durations[-1]] * (frame_count - len(durations)))
    return durations[:frame_count]


def _action_defaults(action_id: str) -> dict[str, object]:
    return dict(DEFAULT_ACTIONS_BY_ID.get(action_id, {}))


def normalize_actions(
    raw_actions: list[object],
    *,
    include_idle: bool = False,
) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []

    for index, raw_action in enumerate(raw_actions):
        if isinstance(raw_action, str):
            raw_action = {"id": raw_action}
        if not isinstance(raw_action, Mapping):
            raise ValueError(f"action #{index + 1} must be a string or mapping")

        raw_id = str(
            raw_action.get("id")
            or raw_action.get("state")
            or raw_action.get("name")
            or raw_action.get("slug")
            or ""
        ).strip()
        raw_label = str(raw_action.get("label") or raw_action.get("title") or "").strip()

        action_id = slugify(raw_id or raw_label or f"action-{index + 1}") or f"action-{index + 1}"
        defaults = _action_defaults(action_id)
        if not defaults and raw_label:
            defaults = _action_defaults(slugify(raw_label))

        label = raw_label or str(defaults.get("label") or display_from_slug(action_id) or f"Action {index + 1}")
        frames = _as_int(raw_action.get("frames"), _as_int(defaults.get("frames"), 6))
        purpose = str(raw_action.get("purpose") or defaults.get("purpose") or f"{label.lower()} loop").strip()
        durations = _normalize_durations(
            raw_action.get("durations"),
            frames,
            defaults.get("durations"),
        )
        normalized.append(
            {
                "id": action_id,
                "label": label,
                "frames": frames,
                "purpose": purpose,
                "durations": durations,
            }
        )

    if include_idle and not any(action["id"] == "idle" for action in normalized):
        idle_defaults = DEFAULT_ACTIONS_BY_ID["idle"]
        normalized.insert(
            0,
            {
                "id": "idle",
                "label": str(idle_defaults["label"]),
                "frames": int(idle_defaults["frames"]),
                "purpose": str(idle_defaults["purpose"]),
                "durations": list(idle_defaults["durations"]),
            },
        )

    deduped: list[dict[str, object]] = []
    seen: dict[str, int] = {}
    for action in normalized:
        action_id = action["id"]
        seen[action_id] = seen.get(action_id, 0) + 1
        if seen[action_id] > 1:
            action_id = f"{action_id}-{seen[action_id]}"
        deduped.append({**action, "id": action_id})

    return [{**action, "row": row_index} for row_index, action in enumerate(deduped)]


def infer_actions_from_prompt(prompt: str) -> list[dict[str, object]]:
    prompt_lower = prompt.lower()
    hits: list[tuple[int, str]] = []
    for action in _DEFAULT_ACTIONS:
        positions = [prompt_lower.find(keyword) for keyword in action.get("keywords", [])]
        positions = [position for position in positions if position >= 0]
        if positions:
            hits.append((min(positions), str(action["id"])))

    raw_actions: list[object] = []
    seen_ids: set[str] = set()
    for _position, action_id in sorted(hits):
        if action_id not in seen_ids:
            raw_actions.append({"id": action_id})
            seen_ids.add(action_id)

    if not raw_actions:
        raw_actions = [{"id": "running"}]
    elif len(raw_actions) == 1 and raw_actions[0] == {"id": "idle"}:
        raw_actions.append({"id": "running"})

    return normalize_actions(raw_actions, include_idle=True)


def _action_payload_from_request(raw_request: Mapping[str, object]) -> list[object]:
    actions = raw_request.get("actions")
    if isinstance(actions, list) and actions:
        return actions
    rows = raw_request.get("rows")
    if isinstance(rows, list) and rows:
        return rows
    return []


def resolve_action_spec(raw_request: Mapping[str, object] | None = None) -> dict[str, object]:
    request = dict(raw_request or {})
    raw_actions = _action_payload_from_request(request)
    prompt = " ".join(
        str(request.get(key) or "").strip()
        for key in ("behavior", "behavior_description", "description", "pet_notes", "prompt")
    ).strip()

    if raw_actions:
        actions = normalize_actions(
            raw_actions,
            include_idle=bool(request.get("include_idle")),
        )
    else:
        actions = infer_actions_from_prompt(prompt)

    atlas_request = request.get("atlas")
    atlas_mapping = atlas_request if isinstance(atlas_request, Mapping) else {}
    cell_width = _read_mapping_int(request, "cell_width", "cellWidth", default=DEFAULT_CELL_WIDTH)
    cell_height = _read_mapping_int(request, "cell_height", "cellHeight", default=DEFAULT_CELL_HEIGHT)
    requested_columns = _read_mapping_int(atlas_mapping, "columns", default=DEFAULT_COLUMNS)
    requested_rows = _read_mapping_int(atlas_mapping, "rows", default=len(actions))
    max_frames = max((int(action["frames"]) for action in actions), default=DEFAULT_COLUMNS)
    columns = max(DEFAULT_COLUMNS, requested_columns, max_frames)
    rows = max(requested_rows, len(actions))

    return {
        "cell_width": cell_width,
        "cell_height": cell_height,
        "atlas": {
            "columns": columns,
            "rows": rows,
            "width": columns * cell_width,
            "height": rows * cell_height,
        },
        "actions": actions,
    }


def load_action_spec_document(path: Path) -> dict[str, object]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return resolve_action_spec(raw if isinstance(raw, Mapping) else {})

