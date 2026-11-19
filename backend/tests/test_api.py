import io
import pytest
from fastapi.testclient import TestClient

from main import app
from services.pdf_service import (
    PDFService,
    EmptyFileError,
    InvalidPDFError,
    CorruptedPDFError,
)

client = TestClient(app)


def create_sample_pdf(text: str = "Hello from VERITAS AI!") -> bytes:
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_empty_page_pdf() -> bytes:
    import fitz

    doc = fitz.open()
    doc.new_page()
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "VERITAS AI Backend"
    assert "version" in data


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["endpoints"]["health"] == "/api/health"
    assert data["endpoints"]["upload"] == "/api/upload"


def test_cors_preflight():
    response = client.options(
        "/api/upload",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_upload_valid_pdf_with_text():
    pdf_content = create_sample_pdf("VERITAS AI Automated Citation Verification System")
    files = {"file": ("research_paper.pdf", io.BytesIO(pdf_content), "application/pdf")}
    response = client.post("/api/upload", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "research_paper.pdf"
    assert data["total_pages"] == 1
    assert "VERITAS AI Automated Citation Verification System" in data["extracted_text"]
    assert data["extraction_status"] == "success"


def test_upload_blank_pdf():
    pdf_content = create_empty_page_pdf()
    files = {"file": ("blank_document.pdf", io.BytesIO(pdf_content), "application/pdf")}
    response = client.post("/api/upload", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "blank_document.pdf"
    assert data["total_pages"] == 1
    assert data["extracted_text"] == ""
    assert data["extraction_status"] == "empty"


def test_upload_non_pdf_file():
    txt_content = b"This is a plain text file, not a PDF."
    files = {"file": ("document.txt", io.BytesIO(txt_content), "text/plain")}
    response = client.post("/api/upload", files=files)
    assert response.status_code == 400
    assert "Only PDF files are accepted" in response.json()["detail"]


def test_upload_empty_file():
    files = {"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")}
    response = client.post("/api/upload", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_upload_corrupted_pdf_invalid_signature():
    corrupted_content = b"This is fake content pretending to be a pdf file."
    files = {"file": ("corrupt.pdf", io.BytesIO(corrupted_content), "application/pdf")}
    response = client.post("/api/upload", files=files)
    assert response.status_code == 400
    assert "header signature" in response.json()["detail"].lower()


def test_upload_corrupted_pdf_broken_body():
    corrupted_pdf = b"%PDF-1.7\nCorrupted binary garbage without PDF trailer or xref."
    files = {"file": ("broken_body.pdf", io.BytesIO(corrupted_pdf), "application/pdf")}
    response = client.post("/api/upload", files=files)
    assert response.status_code == 400
    assert "corrupted" in response.json()["detail"].lower() or "unable to parse" in response.json()["detail"].lower()
