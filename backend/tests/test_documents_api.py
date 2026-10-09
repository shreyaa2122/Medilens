import uuid

from tests.conftest import JPEG_BYTES, PDF_BYTES, PNG_BYTES, upload


def test_upload_returns_201_and_stores_the_file(client, upload_dir):
    response = upload(client, "blood-test.pdf", PDF_BYTES)
    assert response.status_code == 201

    body = response.json()
    assert body["error"] is None
    document = body["data"]
    assert document["file_name"] == "blood-test.pdf"
    assert document["mime_type"] == "application/pdf"
    assert document["file_size_bytes"] == len(PDF_BYTES)
    assert document["processing_status"] == "uploaded"
    assert document["document_type"] == "unknown"
    assert document["upload_date"].endswith(("Z", "+00:00"))

    saved_files = list(upload_dir.iterdir())
    assert len(saved_files) == 1
    # The file on disk must not carry the user's file name
    assert "blood-test" not in saved_files[0].name
    assert saved_files[0].read_bytes() == PDF_BYTES


def test_unsafe_file_name_is_cleaned(client):
    response = upload(client, "../../evil/report.pdf", PDF_BYTES)
    assert response.status_code == 201
    assert response.json()["data"]["file_name"] == "report.pdf"


def test_list_returns_newest_first(client):
    upload(client, "first.pdf", PDF_BYTES)
    upload(client, "second.png", PNG_BYTES)
    names = [d["file_name"] for d in client.get("/api/documents").json()["data"]]
    assert names == ["second.png", "first.pdf"]


def test_get_one_document(client):
    document_id = upload(client, "scan.jpg", JPEG_BYTES).json()["data"]["id"]
    response = client.get(f"/api/documents/{document_id}")
    assert response.status_code == 200
    assert response.json()["data"]["file_name"] == "scan.jpg"


def test_unknown_document_returns_404(client):
    response = client.get(f"/api/documents/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "document_not_found"


def test_invalid_document_id_returns_422(client):
    response = client.get("/api/documents/not-a-uuid")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"


def test_delete_removes_record_and_file(client, upload_dir):
    document_id = upload(client, "report.pdf", PDF_BYTES).json()["data"]["id"]
    assert len(list(upload_dir.iterdir())) == 1

    response = client.delete(f"/api/documents/{document_id}")
    assert response.status_code == 204
    assert list(upload_dir.iterdir()) == []
    assert client.get(f"/api/documents/{document_id}").status_code == 404
    assert client.get("/api/documents").json()["data"] == []


def test_delete_unknown_document_returns_404(client):
    assert client.delete(f"/api/documents/{uuid.uuid4()}").status_code == 404


def test_empty_file_is_rejected_and_nothing_is_stored(client, upload_dir):
    response = upload(client, "report.pdf", b"")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "empty_file"
    assert not upload_dir.exists() or list(upload_dir.iterdir()) == []


def test_oversized_file_is_rejected(client):
    response = upload(client, "report.pdf", PDF_BYTES + b"0" * (1024 * 1024))  # limit is 1 MB in tests
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "file_too_large"


def test_unsupported_type_shows_clear_message(client):
    response = upload(client, "notes.txt", b"hello world")
    assert response.status_code == 415
    error = response.json()["error"]
    assert error["message"] == "Unsupported file type. Please upload a PDF, JPG, JPEG, or PNG."


def test_fake_pdf_is_rejected(client, upload_dir):
    response = upload(client, "report.pdf", b"this is not really a pdf")
    assert response.status_code == 415
    assert not upload_dir.exists() or list(upload_dir.iterdir()) == []


def test_missing_file_field_returns_422(client):
    response = client.post("/api/documents/upload")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"
