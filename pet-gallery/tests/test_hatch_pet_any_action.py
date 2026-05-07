import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ACTION_SPEC_PATH = Path("/root/.codex/skills/hatch-pet-any-action/scripts/action_spec.py")
PACKAGE_SCRIPT_PATH = Path("/root/.codex/skills/hatch-pet-any-action/scripts/package_custom_pet.py")
PREPARE_SCRIPT_PATH = Path("/root/.codex/skills/hatch-pet-any-action/scripts/prepare_pet_run.py")
EXTRACT_SCRIPT_PATH = Path("/root/.codex/skills/hatch-pet-any-action/scripts/extract_strip_frames.py")
GENERATE_SCRIPT_PATH = Path("/root/.codex/skills/hatch-pet-any-action/scripts/generate_pet_images.py")


def load_action_spec_module():
    spec = importlib.util.spec_from_file_location("hatch_pet_any_action_action_spec", ACTION_SPEC_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {ACTION_SPEC_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HatchPetAnyActionTests(unittest.TestCase):
    def test_infer_actions_adds_idle_and_assigns_rows(self):
        module = load_action_spec_module()

        actions = module.infer_actions_from_prompt(
            "A fox pet that should feel busy coding, then sleep, then celebrate with a spin."
        )

        self.assertGreaterEqual(len(actions), 4)
        self.assertEqual("idle", actions[0]["id"])
        self.assertEqual(list(range(len(actions))), [action["row"] for action in actions])

    def test_infer_actions_supports_more_than_nine_actions(self):
        module = load_action_spec_module()

        actions = module.normalize_actions(
            [
                {"label": f"Action {index}", "frames": 4 + (index % 3)}
                for index in range(11)
            ]
        )

        self.assertEqual(11, len(actions))
        self.assertEqual(10, actions[-1]["row"])
        self.assertEqual("action-10", actions[-1]["id"])

    def test_resolve_action_spec_expands_rows_and_preserves_default_columns(self):
        module = load_action_spec_module()

        spec = module.resolve_action_spec(
            {
                "actions": [
                    {"label": f"Pose {index + 1}", "frames": 4}
                    for index in range(11)
                ]
            }
        )

        self.assertEqual(8, spec["atlas"]["columns"])
        self.assertEqual(11, spec["atlas"]["rows"])
        self.assertEqual(192, spec["cell_width"])
        self.assertEqual(208, spec["cell_height"])
        self.assertEqual(list(range(11)), [action["row"] for action in spec["actions"]])

    def test_package_script_accepts_dynamic_atlas_and_writes_extended_manifest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            spritesheet_path = temp_path / "spritesheet.png"
            output_dir = temp_path / "pet-output"
            Image.new("RGBA", (1536, 2288), (0, 0, 0, 0)).save(spritesheet_path)

            result = subprocess.run(
                [
                    "python3",
                    str(PACKAGE_SCRIPT_PATH),
                    "--pet-name",
                    "Any Action Fox",
                    "--display-name",
                    "Any Action Fox",
                    "--description",
                    "Dynamic action fox.",
                    "--spritesheet",
                    str(spritesheet_path),
                    "--cell-width",
                    "192",
                    "--cell-height",
                    "208",
                    "--atlas-columns",
                    "8",
                    "--atlas-rows",
                    "11",
                    "--actions-json",
                    json.dumps(
                        [
                            {"id": "idle", "label": "Idle", "row": 0, "frames": 6},
                            {"id": "coding", "label": "Coding", "row": 10, "frames": 8},
                        ]
                    ),
                    "--output-dir",
                    str(output_dir),
                    "--force",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(0, result.returncode, result.stderr)
            manifest = json.loads((output_dir / "pet.json").read_text(encoding="utf-8"))
            self.assertEqual(192, manifest["cellWidth"])
            self.assertEqual(208, manifest["cellHeight"])
            self.assertEqual(8, manifest["atlas"]["columns"])
            self.assertEqual(11, manifest["atlas"]["rows"])
            self.assertEqual(2, len(manifest["actions"]))

    def test_prepare_pet_run_module_is_importable(self):
        module = load_module(PREPARE_SCRIPT_PATH, "hatch_pet_any_action_prepare")
        self.assertTrue(hasattr(module, "main"))

    def test_extract_strip_frames_module_is_importable(self):
        module = load_module(EXTRACT_SCRIPT_PATH, "hatch_pet_any_action_extract")
        self.assertTrue(hasattr(module, "main"))

    def test_running_left_without_running_right_is_not_blocked(self):
        module = load_module(PREPARE_SCRIPT_PATH, "hatch_pet_any_action_prepare_dynamic_jobs")

        jobs = module.make_jobs(
            Path("/tmp/hatch-pet-any-action"),
            copied_refs=[],
            actions=[
                {"id": "idle", "label": "Idle", "row": 0, "frames": 6},
                {"id": "running-left", "label": "Running Left", "row": 1, "frames": 8},
            ],
        )

        running_left = next(job for job in jobs if job["id"] == "running-left")
        self.assertEqual(["base"], running_left["depends_on"])
        self.assertEqual({}, running_left["mirror_policy"])
        self.assertFalse(
            any(item["path"] == "decoded/running-right.png" for item in running_left["input_images"])
        )

    def test_generate_pet_images_states_follow_manifest_jobs(self):
        module = load_module(GENERATE_SCRIPT_PATH, "hatch_pet_any_action_generate")
        manifest = {
            "jobs": [
                {"id": "base"},
                {"id": "idle"},
                {"id": "coding"},
                {"id": "sleeping"},
            ]
        }

        valid_states = module.available_states(manifest)
        self.assertEqual(["idle", "coding", "sleeping"], valid_states)
        self.assertEqual(valid_states, module.parse_states("all", valid_states=valid_states))
        self.assertEqual(["coding", "sleeping"], module.parse_states("coding,sleeping", valid_states=valid_states))

        with self.assertRaises(SystemExit):
            module.parse_states("review", valid_states=valid_states)


if __name__ == "__main__":
    unittest.main()
