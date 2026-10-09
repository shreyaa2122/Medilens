import pytest

from app.services.storage_service import StorageService


def test_save_uses_random_name_and_writes_content(tmp_path):
    storage = StorageService(str(tmp_path / "files"))
    stored_name = storage.save(b"hello", "pdf")
    assert stored_name.endswith(".pdf")
    assert (tmp_path / "files" / stored_name).read_bytes() == b"hello"


def test_two_saves_never_share_a_name(tmp_path):
    storage = StorageService(str(tmp_path))
    assert storage.save(b"a", "png") != storage.save(b"a", "png")


def test_delete_removes_file_and_is_safe_to_repeat(tmp_path):
    storage = StorageService(str(tmp_path))
    stored_name = storage.save(b"hello", "pdf")
    storage.delete(stored_name)
    assert not (tmp_path / stored_name).exists()
    storage.delete(stored_name)  # deleting twice must not raise


def test_refuses_paths_outside_the_upload_folder(tmp_path):
    storage = StorageService(str(tmp_path / "files"))
    with pytest.raises(ValueError):
        storage.delete("../outside.pdf")
