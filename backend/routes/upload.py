from fastapi import APIRouter, File, UploadFile, HTTPException, status
from models.schemas import PDFExtractionResponse, ErrorResponse
from services.pdf_service import (
    PDFService,
    InvalidPDFError,
    CorruptedPDFError,
    EmptyFileError,
)

router = APIRouter(tags=["Upload"])


@router.post(
    "/upload",
    response_model=PDFExtractionResponse,
    summary="Upload and extract text from a PDF document",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Invalid, empty, or corrupted PDF",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Server processing error",
        },
    },
)
async def upload_pdf(file: UploadFile = File(...)) -> PDFExtractionResponse:
    """Accepts a PDF file upload, validates it, and extracts plain text.

    Returns:
        JSON response with filename, total_pages, extracted_text, and extraction_status.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename.",
        )

    # Validate file extension
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{file.filename}'. Only PDF files are accepted.",
        )

    # Read uploaded bytes safely
    try:
        content = await file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file content: {str(exc)}",
        )

    # Delegate extraction and parsing to PDFService
    try:
        result = PDFService.extract_text(file_bytes=content, filename=file.filename)
        return PDFExtractionResponse(**result)
    except (EmptyFileError, InvalidPDFError, CorruptedPDFError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while processing the PDF: {str(exc)}",
        )
