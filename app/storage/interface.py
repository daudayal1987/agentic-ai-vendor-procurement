from abc import ABC, abstractmethod
from typing import BinaryIO


class ObjectStorage(ABC):
    """Abstract interface for binary object storage."""

    @abstractmethod
    def upload(
        self,
        object_key: str,
        content: BinaryIO,
        content_type: str | None = None,
    ) -> None:
        """Store an object."""
        raise NotImplementedError

    @abstractmethod
    def download(
        self,
        object_key: str,
    ) -> bytes:
        """Retrieve an object."""
        raise NotImplementedError

    @abstractmethod
    def delete(
        self,
        object_key: str,
    ) -> None:
        """Delete an object."""
        raise NotImplementedError