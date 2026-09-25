from io import BytesIO

from app.storage.local import LocalObjectStorage


def test_upload_download_delete(tmp_path):
    storage = LocalObjectStorage(tmp_path)

    object_key = "documents/test-document.txt"
    content = b"Enterprise Document Intelligence"

    storage.upload(
        object_key=object_key,
        content=BytesIO(content),
        content_type="text/plain",
    )

    assert (tmp_path / object_key).exists()

    downloaded = storage.download(object_key)

    assert downloaded == content

    storage.delete(object_key)

    assert not (tmp_path / object_key).exists()