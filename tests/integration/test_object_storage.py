from io import BytesIO

from app.storage.factory import get_object_storage


def test_object_storage_lifecycle():
    storage = get_object_storage()

    object_key = "test/day3/sample.txt"
    original_content = b"Day 3 object storage verification"

    storage.upload(
        object_key=object_key,
        content=BytesIO(original_content),
        content_type="text/plain",
    )

    downloaded_content = storage.download(object_key)

    assert downloaded_content == original_content

    storage.delete(object_key)

    try:
        storage.download(object_key)
        assert False, "Deleted object should not be downloadable"
    except FileNotFoundError:
        pass