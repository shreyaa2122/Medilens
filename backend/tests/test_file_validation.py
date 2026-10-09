import pytest

from app.core.errors import AppError
from app.core.security import sanitize_filename
from app.services.file_validation import validate_upload
from tests.conftest import JPEG_BYTES, PDF_BYTES, PNG_BYTES

MAX = 1024 * 1024


@pytest.mark.parametrize(
    "name, content, extension, mime",
    [
        ("report.pdf", PDF_BYTES, "pdf", "application/pdf"),
        ("scan.png", PNG_BYTES, "png", "image/png"),
        ("photo.jpg", JPEG_BYTES, "jpg", "image/jpeg"),
        ("photo.jpeg", JPEG_BYTES, "jpg", "image/jpeg"),
        ("REPORT.PDF", PDF_BYTES, "pdf", "application/pdf"),
    ],
)
def test_accepts_supported_files(name, content, extension, mime):
    result = validate_upload(name, content, MAX)
    assert result.extension == extension
    assert result.mime_type == mime
    assert result.size_bytes == len(content)


def test_rejects_empty_file():
    with pytest.raises(AppError) as error:
        validate_upload("report.pdf", b"", MAX)
    assert error.value.code == "empty_file"
    assert error.value.status_code == 400


def test_rejects_oversized_file():
    with pytest.raises(AppError) as error:
        validate_upload("report.pdf", PDF_BYTES + b"0" * MAX, MAX)
    assert error.value.code == "file_too_large"
    assert error.value.status_code == 413


@pytest.mark.parametrize("name", ["virus.exe", "notes.txt", "noextension", "archive.pdf.zip"])
def test_rejects_unsupported_extension(name):
    with pytest.raises(AppError) as error:
        validate_upload(name, PDF_BYTES, MAX)
    assert error.value.code == "unsupported_file_type"
    assert error.value.message == "Unsupported file type. Please upload a PDF, JPG, JPEG, or PNG."


def test_rejects_text_file_renamed_to_pdf():
    with pytest.raises(AppError) as error:
        validate_upload("report.pdf", b"just some plain text, not a pdf", MAX)
    assert error.value.code == "unsupported_file_type"


def test_rejects_png_renamed_to_pdf():
    with pytest.raises(AppError) as error:
        validate_upload("report.pdf", PNG_BYTES, MAX)
    assert error.value.code == "file_content_mismatch"


def test_sanitize_removes_folder_paths():
    assert sanitize_filename("../../etc/passwd") == "passwd"
    assert sanitize_filename("C:\\Users\\me\\report.pdf") == "report.pdf"


def test_sanitize_handles_empty_and_control_characters():
    assert sanitize_filename(None) == "document"
    assert sanitize_filename("") == "document"
    assert sanitize_filename("..") == "document"
    assert sanitize_filename("re\x00port\n.pdf") == "report.pdf"


def test_sanitize_truncates_long_names_but_keeps_extension():
    result = sanitize_filename("a" * 300 + ".pdf", max_length=50)
    assert len(result) == 50
    assert result.endswith(".pdf")
