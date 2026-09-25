from app.common.config import get_settings
from app.storage.interface import ObjectStorage
from app.storage.local import LocalObjectStorage


def get_object_storage() -> ObjectStorage:
    settings = get_settings()

    if settings.storage_backend == "local":
        return LocalObjectStorage(
            base_path=settings.storage_base_path,
        )

    raise ValueError(
        f"Unsupported storage backend: {settings.storage_backend}"
    )