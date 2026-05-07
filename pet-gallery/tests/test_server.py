import base64
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from server import DELETE_PASSWORD, PetError, PetStore


PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO5T2ioAAAAASUVORK5CYII="
)


class PetStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        (self.base_dir / "assets").mkdir()
        (self.base_dir / "assets" / "foxy-spritesheet.webp").write_bytes(b"bundled-webp")
        self.store = PetStore(base_dir=self.base_dir)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_list_pets_includes_bundled_entries(self):
        pets = self.store.list_pets()

        self.assertEqual(1, len(pets))
        self.assertEqual("foxy", pets[0]["id"])
        self.assertEqual("bundled", pets[0]["source"])

    def test_save_uploaded_pet_persists_files_and_metadata(self):
        pet = self.store.save_uploaded_pet(
            manifest={
                "id": "snowy",
                "displayName": "Snowy",
                "description": "Snow fox",
            },
            spritesheet_name="spritesheet.png",
            spritesheet_bytes=PNG_BYTES,
            overwrite=False,
        )

        self.assertEqual("snowy", pet["id"])
        self.assertEqual("uploaded", pet["source"])
        self.assertTrue((self.base_dir / "data" / "pets" / "snowy" / "pet.json").exists())
        self.assertTrue((self.base_dir / "data" / "pets" / "snowy" / "spritesheet.png").exists())

        saved_manifest = json.loads((self.base_dir / "data" / "pets" / "snowy" / "pet.json").read_text())
        self.assertEqual("spritesheet.png", saved_manifest["spritesheetPath"])

    def test_save_uploaded_pet_rejects_conflict_without_overwrite(self):
        self.store.save_uploaded_pet(
            manifest={"id": "snowy", "displayName": "Snowy"},
            spritesheet_name="spritesheet.png",
            spritesheet_bytes=PNG_BYTES,
            overwrite=False,
        )

        with self.assertRaises(PetError):
            self.store.save_uploaded_pet(
                manifest={"id": "snowy", "displayName": "Snowy Two"},
                spritesheet_name="spritesheet.webp",
                spritesheet_bytes=b"new-webp",
                overwrite=False,
            )

    def test_save_uploaded_pet_overwrites_existing_uploaded_pet(self):
        self.store.save_uploaded_pet(
            manifest={"id": "snowy", "displayName": "Snowy"},
            spritesheet_name="spritesheet.png",
            spritesheet_bytes=PNG_BYTES,
            overwrite=False,
        )

        pet = self.store.save_uploaded_pet(
            manifest={"id": "snowy", "displayName": "Snowy Two"},
            spritesheet_name="spritesheet.webp",
            spritesheet_bytes=b"new-webp",
            overwrite=True,
        )

        self.assertEqual("Snowy Two", pet["displayName"])
        self.assertTrue((self.base_dir / "data" / "pets" / "snowy" / "spritesheet.webp").exists())
        self.assertFalse((self.base_dir / "data" / "pets" / "snowy" / "spritesheet.png").exists())

    def test_delete_uploaded_pet_requires_correct_password(self):
        self.store.save_uploaded_pet(
            manifest={"id": "snowy", "displayName": "Snowy"},
            spritesheet_name="spritesheet.png",
            spritesheet_bytes=PNG_BYTES,
            overwrite=False,
        )

        with self.assertRaises(PetError):
            self.store.delete_uploaded_pet("snowy", password="bad")

        self.store.delete_uploaded_pet("snowy", password=DELETE_PASSWORD)

        ids = [pet["id"] for pet in self.store.list_pets()]
        self.assertNotIn("snowy", ids)

    def test_download_pet_package_contains_manifest_and_spritesheet(self):
        self.store.save_uploaded_pet(
            manifest={"id": "snowy", "displayName": "Snowy"},
            spritesheet_name="spritesheet.png",
            spritesheet_bytes=PNG_BYTES,
            overwrite=False,
        )

        archive_name, archive_bytes = self.store.build_download_package("snowy")

        self.assertEqual("snowy.zip", archive_name)
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
            self.assertEqual(["pet.json", "spritesheet.png"], sorted(archive.namelist()))
            saved_manifest = json.loads(archive.read("pet.json").decode("utf-8"))
            self.assertEqual("snowy", saved_manifest["id"])


class FrontendStylesTests(unittest.TestCase):
    def test_delete_modal_hidden_state_is_explicitly_preserved(self):
        styles = (Path(__file__).resolve().parent.parent / "styles.css").read_text(encoding="utf-8")

        self.assertIn(".modal-shell[hidden]", styles)


if __name__ == "__main__":
    unittest.main()
