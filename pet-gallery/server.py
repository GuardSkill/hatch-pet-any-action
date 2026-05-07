#!/usr/bin/env python3

from __future__ import annotations

import argparse
import base64
import io
import json
import shutil
import zipfile
from copy import deepcopy
from dataclasses import dataclass
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 13645
DELETE_PASSWORD = "104228"
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "pets"
INDEX_FILE = DATA_DIR / "index.json"

BUNDLED_PETS = [
    {
        "id": "foxy",
        "displayName": "Foxy",
        "description": "Pixel fox Codex pet",
        "spritesheetPath": "assets/foxy-spritesheet.webp",
    }
]


class PetError(Exception):
    def __init__(self, message: str, status: int = HTTPStatus.BAD_REQUEST):
        super().__init__(message)
        self.message = message
        self.status = int(status)


@dataclass
class StoredPet:
    manifest: dict[str, Any]
    spritesheet_name: str
    spritesheet_bytes: bytes


class PetStore:
    def __init__(self, base_dir: Path = BASE_DIR):
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / "data" / "pets"
        self.index_file = self.data_dir / "index.json"
        self.ensure_storage()

    def ensure_storage(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.index_file.exists():
            self.index_file.write_text("{}", encoding="utf-8")

    def list_pets(self) -> list[dict[str, Any]]:
        pets = self._bundled_records()
        uploaded = sorted(self._uploaded_records(), key=lambda pet: pet["displayName"].lower())
        return pets + uploaded

    def save_uploaded_pet(
        self,
        manifest: dict[str, Any],
        spritesheet_name: str,
        spritesheet_bytes: bytes,
        overwrite: bool,
    ) -> dict[str, Any]:
        if not isinstance(manifest, dict):
            raise PetError("Manifest must be an object.")
        pet_id = self._normalize_id(manifest.get("id") or manifest.get("displayName") or "uploaded-pet")
        if pet_id in self._bundled_map():
            raise PetError(f"Pet id '{pet_id}' is reserved by a bundled pet.", HTTPStatus.CONFLICT)
        index = self._load_index()
        if pet_id in index and not overwrite:
            raise PetError(f"Pet id '{pet_id}' already exists.", HTTPStatus.CONFLICT)
        if pet_id in index and overwrite:
            self._delete_pet_dir(pet_id)

        extension = self._normalize_extension(spritesheet_name)
        pet_dir = self.data_dir / pet_id
        pet_dir.mkdir(parents=True, exist_ok=True)

        cleaned_manifest = {
            **deepcopy(manifest),
            "id": pet_id,
            "displayName": manifest.get("displayName") or pet_id,
            "description": manifest.get("description") or "Uploaded Codex pet",
            "spritesheetPath": f"spritesheet{extension}",
        }
        (pet_dir / "pet.json").write_text(
            json.dumps(cleaned_manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (pet_dir / f"spritesheet{extension}").write_bytes(spritesheet_bytes)

        index[pet_id] = {
            "displayName": cleaned_manifest["displayName"],
            "description": cleaned_manifest["description"],
            "spritesheetFile": f"spritesheet{extension}",
        }
        self._save_index(index)
        return self.get_pet_record(pet_id)

    def delete_uploaded_pet(self, pet_id: str, password: str) -> None:
        if password != DELETE_PASSWORD:
            raise PetError("Incorrect password.", HTTPStatus.FORBIDDEN)
        index = self._load_index()
        if pet_id not in index:
            if pet_id in self._bundled_map():
                raise PetError("Bundled pets cannot be deleted.", HTTPStatus.BAD_REQUEST)
            raise PetError("Pet not found.", HTTPStatus.NOT_FOUND)
        self._delete_pet_dir(pet_id)
        index.pop(pet_id, None)
        self._save_index(index)

    def build_download_package(self, pet_id: str) -> tuple[str, bytes]:
        stored_pet = self._load_pet_files(pet_id)
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as package:
            package.writestr(
                "pet.json",
                json.dumps(stored_pet.manifest, ensure_ascii=False, indent=2),
            )
            package.writestr(stored_pet.spritesheet_name, stored_pet.spritesheet_bytes)
        return f"{pet_id}.zip", archive.getvalue()

    def get_manifest(self, pet_id: str) -> dict[str, Any]:
        stored_pet = self._load_pet_files(pet_id)
        return stored_pet.manifest

    def get_pet_record(self, pet_id: str) -> dict[str, Any]:
        for pet in self.list_pets():
            if pet["id"] == pet_id:
                return pet
        raise PetError("Pet not found.", HTTPStatus.NOT_FOUND)

    def _bundled_records(self) -> list[dict[str, Any]]:
        return [
            {
                "id": pet["id"],
                "displayName": pet["displayName"],
                "description": pet["description"],
                "source": "bundled",
                "spritesheetUrl": f"/{pet['spritesheetPath']}",
                "manifestUrl": f"/api/pets/{pet['id']}/manifest",
                "downloadUrl": f"/api/pets/{pet['id']}/download",
                "canDelete": False,
            }
            for pet in BUNDLED_PETS
        ]

    def _uploaded_records(self) -> list[dict[str, Any]]:
        index = self._load_index()
        records = []
        for pet_id, entry in index.items():
            records.append(
                {
                    "id": pet_id,
                    "displayName": entry["displayName"],
                    "description": entry["description"],
                    "source": "uploaded",
                    "spritesheetUrl": f"/data/pets/{pet_id}/{entry['spritesheetFile']}",
                    "manifestUrl": f"/api/pets/{pet_id}/manifest",
                    "downloadUrl": f"/api/pets/{pet_id}/download",
                    "canDelete": True,
                }
            )
        return records

    def _load_pet_files(self, pet_id: str) -> StoredPet:
        bundled = self._bundled_map()
        if pet_id in bundled:
            pet = bundled[pet_id]
            spritesheet_path = self.base_dir / pet["spritesheetPath"]
            return StoredPet(
                manifest={
                    "id": pet["id"],
                    "displayName": pet["displayName"],
                    "description": pet["description"],
                    "spritesheetPath": Path(pet["spritesheetPath"]).name,
                },
                spritesheet_name=Path(pet["spritesheetPath"]).name,
                spritesheet_bytes=spritesheet_path.read_bytes(),
            )

        index = self._load_index()
        entry = index.get(pet_id)
        if not entry:
            raise PetError("Pet not found.", HTTPStatus.NOT_FOUND)
        pet_dir = self.data_dir / pet_id
        manifest_path = pet_dir / "pet.json"
        spritesheet_name = entry["spritesheetFile"]
        spritesheet_path = pet_dir / spritesheet_name
        return StoredPet(
            manifest=json.loads(manifest_path.read_text(encoding="utf-8")),
            spritesheet_name=spritesheet_name,
            spritesheet_bytes=spritesheet_path.read_bytes(),
        )

    def _load_index(self) -> dict[str, dict[str, str]]:
        try:
            content = json.loads(self.index_file.read_text(encoding="utf-8") or "{}")
        except json.JSONDecodeError as error:
            raise PetError(f"Could not parse pet index: {error}", HTTPStatus.INTERNAL_SERVER_ERROR) from error
        if not isinstance(content, dict):
            raise PetError("Pet index is corrupted.", HTTPStatus.INTERNAL_SERVER_ERROR)
        return content

    def _save_index(self, content: dict[str, dict[str, str]]) -> None:
        self.index_file.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")

    def _delete_pet_dir(self, pet_id: str) -> None:
        shutil.rmtree(self.data_dir / pet_id, ignore_errors=True)

    def _bundled_map(self) -> dict[str, dict[str, str]]:
        return {pet["id"]: pet for pet in BUNDLED_PETS}

    @staticmethod
    def _normalize_extension(filename: str) -> str:
        suffix = Path(filename or "").suffix.lower()
        if suffix not in {".png", ".webp"}:
            raise PetError("Spritesheet must be a .png or .webp file.")
        return suffix

    @staticmethod
    def _normalize_id(value: str) -> str:
        slug = "".join(char.lower() if char.isalnum() else "-" for char in str(value))
        slug = "-".join(filter(None, slug.split("-")))
        return slug[:40] or "uploaded-pet"


class PetGalleryHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, directory: str, store: PetStore, **kwargs: Any):
        self.store = store
        super().__init__(*args, directory=directory, **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/pets":
            self._respond_json({"pets": self.store.list_pets()})
            return
        if parsed.path.startswith("/api/pets/") and parsed.path.endswith("/download"):
            pet_id = self._extract_pet_id(parsed.path, suffix="/download")
            archive_name, archive_bytes = self.store.build_download_package(pet_id)
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Length", str(len(archive_bytes)))
            self.send_header("Content-Disposition", f'attachment; filename="{archive_name}"')
            self.end_headers()
            self.wfile.write(archive_bytes)
            return
        if parsed.path.startswith("/api/pets/") and parsed.path.endswith("/manifest"):
            pet_id = self._extract_pet_id(parsed.path, suffix="/manifest")
            self._respond_json(self.store.get_manifest(pet_id))
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/api/pets":
            self._respond_error("Not found.", HTTPStatus.NOT_FOUND)
            return
        payload = self._read_json_body()
        manifest = payload.get("manifest")
        spritesheet_name = payload.get("spritesheetName", "")
        spritesheet_content = payload.get("spritesheetContent", "")
        overwrite = bool(payload.get("overwrite"))
        spritesheet_bytes = decode_base64_content(spritesheet_content)
        pet = self.store.save_uploaded_pet(
            manifest=manifest,
            spritesheet_name=spritesheet_name,
            spritesheet_bytes=spritesheet_bytes,
            overwrite=overwrite,
        )
        self._respond_json({"pet": pet}, status=HTTPStatus.CREATED)

    def do_DELETE(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/pets/"):
            self._respond_error("Not found.", HTTPStatus.NOT_FOUND)
            return
        pet_id = self._extract_pet_id(parsed.path)
        payload = self._read_json_body()
        self.store.delete_uploaded_pet(pet_id, password=str(payload.get("password", "")))
        self._respond_json({"ok": True})

    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:
        detail = message or HTTPStatus(code).phrase
        self._respond_error(detail, code)

    def log_message(self, format: str, *args: Any) -> None:
        super().log_message(format, *args)

    def handle_one_request(self) -> None:
        try:
            super().handle_one_request()
        except PetError as error:
            self._respond_error(error.message, error.status)
        except Exception as error:  # noqa: BLE001
            self._respond_error(str(error), HTTPStatus.INTERNAL_SERVER_ERROR)

    def _extract_pet_id(self, path: str, suffix: str = "") -> str:
        trimmed = path.removeprefix("/api/pets/")
        if suffix:
            trimmed = trimmed.removesuffix(suffix)
        return unquote(trimmed.strip("/"))

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError as error:
            raise PetError(f"Invalid JSON body: {error}", HTTPStatus.BAD_REQUEST) from error
        if not isinstance(payload, dict):
            raise PetError("JSON body must be an object.", HTTPStatus.BAD_REQUEST)
        return payload

    def _respond_json(self, payload: dict[str, Any] | list[Any], status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _respond_error(self, message: str, status: int) -> None:
        self._respond_json({"error": message}, status=status)


def decode_base64_content(content: str) -> bytes:
    if not content:
        raise PetError("Spritesheet content is required.")
    encoded = content.split(",", 1)[1] if "," in content else content
    try:
        return base64.b64decode(encoded, validate=True)
    except Exception as error:  # noqa: BLE001
        raise PetError("Spritesheet content is not valid base64.") from error


def create_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, base_dir: Path = BASE_DIR) -> ThreadingHTTPServer:
    store = PetStore(base_dir=base_dir)
    directory = str(base_dir)

    def handler(*args: Any, **kwargs: Any) -> PetGalleryHandler:
        return PetGalleryHandler(*args, directory=directory, store=store, **kwargs)

    return ThreadingHTTPServer((host, port), handler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the pet gallery with a shared pet library.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    server = create_server(host=args.host, port=args.port)
    print(f"Pet Gallery server listening on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
