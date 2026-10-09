import uuid

from sqlalchemy import func, select

from app.core.config import Settings
from app.db.models import Document, DocumentPage
from app.main import create_app
from fastapi.testclient import TestClient
from tests.conftest import PDF_BYTES, upload
from tests.sample_documents import (
    blur,
    make_digital_pdf,
    make_password_protected_pdf,
    make_scanned_pdf,
    render_report,
    to_png_bytes,
    words_found,
)
from tests.test_ocr_service import TOTAL_WORDS, requires_tesseract

# Note: the test client waits for background work, so by the time upload() returns the
# document has already been processed.


def get_document(client, document_id):
    return client.get(f"/api/documents/{document_id}").json()["data"]


def test_digital_pdf_is_processed_end_to_end(client):
    created = upload(client, "report.pdf", make_digital_pdf()).json()["data"]
    assert created["processing_status"] == "uploaded"  # response is sent before processing

    document = get_document(client, created["id"])
    assert document["processing_status"] == "completed"
    assert document["error_code"] is None and document["error_message"] is None

    pages = client.get(f"/api/documents/{created['id']}/pages").json()["data"]
    assert len(pages) == 1
    assert pages[0]["method"] == "native"
    assert pages[0]["ocr_confidence"] is None
    assert words_found(pages[0]["text"]) == TOTAL_WORDS


@requires_tesseract
def test_scanned_pdf_and_photo_are_processed_with_ocr(client):
    for name, content in [
        ("scan.pdf", make_scanned_pdf(render_report())),
        ("photo.png", to_png_bytes(render_report())),
    ]:
        document_id = upload(client, name, content).json()["data"]["id"]
        assert get_document(client, document_id)["processing_status"] == "completed"
        page = client.get(f"/api/documents/{document_id}/pages").json()["data"][0]
        assert page["method"] == "ocr"
        assert page["ocr_confidence"] >= 0.8
        assert words_found(page["text"]) >= TOTAL_WORDS - 1


@requires_tesseract
def test_blurry_photo_ends_with_low_confidence_or_a_clear_failure(client):
    document_id = upload(client, "blurry.png", to_png_bytes(blur(render_report(), 4))).json()["data"]["id"]
    document = get_document(client, document_id)
    if document["processing_status"] == "completed":
        page = client.get(f"/api/documents/{document_id}/pages").json()["data"][0]
        assert page["ocr_confidence"] < 0.70
    else:
        assert document["error_code"] == "no_text_found"
        assert "clearer" in document["error_message"]


def test_unreadable_file_fails_safely_with_a_clean_message(client):
    document_id = upload(client, "broken.pdf", PDF_BYTES).json()["data"]["id"]
    document = get_document(client, document_id)
    assert document["processing_status"] == "failed"
    assert document["error_code"] == "unreadable_document"
    assert "could not be opened" in document["error_message"]
    assert "Traceback" not in str(document)
    assert client.get(f"/api/documents/{document_id}/pages").json()["data"] == []


def test_password_protected_pdf_gives_specific_message(client):
    document_id = upload(client, "locked.pdf", make_password_protected_pdf()).json()["data"]["id"]
    document = get_document(client, document_id)
    assert document["error_code"] == "password_protected_pdf"
    assert "password" in document["error_message"].lower()


def test_retry_runs_processing_again(client):
    document_id = upload(client, "broken.pdf", PDF_BYTES).json()["data"]["id"]
    response = client.post(f"/api/documents/{document_id}/retry")
    assert response.status_code == 202
    assert response.json()["data"]["processing_status"] == "processing"
    assert get_document(client, document_id)["processing_status"] == "failed"  # still broken


def test_retry_does_not_duplicate_pages(client):
    document_id = upload(client, "report.pdf", make_digital_pdf()).json()["data"]["id"]
    client.post(f"/api/documents/{document_id}/retry")
    pages = client.get(f"/api/documents/{document_id}/pages").json()["data"]
    assert len(pages) == 1


def test_retry_unknown_document_returns_404(client):
    assert client.post(f"/api/documents/{uuid.uuid4()}/retry").status_code == 404


def test_retry_is_refused_while_processing(client):
    document_id = upload(client, "report.pdf", make_digital_pdf()).json()["data"]["id"]
    with client.app.state.session_factory() as db:
        db.get(Document, uuid.UUID(document_id)).processing_status = "processing"
        db.commit()
    response = client.post(f"/api/documents/{document_id}/retry")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "already_processing"


def test_deleting_a_document_also_deletes_its_extracted_text(client):
    document_id = upload(client, "report.pdf", make_digital_pdf()).json()["data"]["id"]
    with client.app.state.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(DocumentPage)) == 1
    assert client.delete(f"/api/documents/{document_id}").status_code == 204
    with client.app.state.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(DocumentPage)) == 0


def test_pages_of_unknown_document_return_404(client):
    assert client.get(f"/api/documents/{uuid.uuid4()}/pages").status_code == 404


def test_documents_cut_off_by_a_restart_are_marked_failed(client, settings):
    document_id = upload(client, "report.pdf", make_digital_pdf()).json()["data"]["id"]
    with client.app.state.session_factory() as db:
        db.get(Document, uuid.UUID(document_id)).processing_status = "processing"
        db.commit()

    with TestClient(create_app(settings)) as restarted:  # simulates restarting the server
        document = restarted.get(f"/api/documents/{document_id}").json()["data"]
    assert document["processing_status"] == "failed"
    assert document["error_code"] == "interrupted"
    assert "interrupted" in document["error_message"]


def test_health_reports_whether_ocr_is_available(client):
    data = client.get("/api/health").json()["data"]
    assert isinstance(data["ocr_available"], bool)


def test_extracted_text_is_never_written_to_the_logs(client, caplog):
    caplog.set_level("DEBUG")
    upload(client, "Jane-Doe-report.pdf", make_digital_pdf())
    log_text = caplog.text
    assert "Hemoglobin" not in log_text and "10.2" not in log_text
    assert "Jane-Doe" not in log_text
