from pathlib import Path
from typing import BinaryIO

from app.storage.interface import ObjectStorage


class LocalObjectStorage(ObjectStorage):
    """Filesystem-backed object storage implementation."""

    def __init__(self, base_path: str | Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, object_key: str) -> Path:
        path = self.base_path / object_key

        # Prevent path traversal outside the storage root.
        resolved = path.resolve()
        base = self.base_path.resolve()

        if not resolved.is_relative_to(base):
            raise ValueError("Invalid object key")

        return resolved

    def upload(
        self,
        object_key: str,
        content: BinaryIO,
        content_type: str | None = None,
    ) -> None:
        path = self._resolve_path(object_key)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("wb") as destination:
            destination.write(content.read())

    def download(self, object_key: str) -> bytes:
        path = self._resolve_path(object_key)

        if not path.is_file():
            raise FileNotFoundError(f"Object not found: {object_key}")

        return path.read_bytes()

    def delete(self, object_key: str) -> None:
        path = self._resolve_path(object_key)

        if path.exists():
            path.unlink()