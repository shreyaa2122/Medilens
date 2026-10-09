import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

# Minimal byte strings that start like real files. They are enough for upload
# validation; real parsing is tested separately when documents are processed.
PDF_BYTES = b"%PDF-1.4\n%fake test document\n" + b"0" * 200
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"0" * 200
JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"0" * 200


@pytest.fixture
def upload_dir(tmp_path):
    return tmp_path / "uploads"


@pytest.fixture
def client(tmp_path, upload_dir):
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        upload_dir=str(upload_dir),
        max_upload_mb=1,
    )
    # "with" runs app startup, which creates the tables and the default user.
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def upload(client, name, content, content_type="application/octet-stream"):
    return client.post("/api/documents/upload", files={"file": (name, content, content_type)})
