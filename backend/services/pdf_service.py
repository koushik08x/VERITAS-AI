"""PDF extraction service using PyMuPDF (fitz).

Handles file validation, text extraction, and edge cases such as empty,
invalid, or corrupted PDF files.
"""

from typing import Dict, Any
import fitz  # PyMuPDF


class PDFServiceError(Exception):
    """Base exception for PDF processing errors."""
    pass


class InvalidPDFError(PDFServiceError):
    """Raised when the uploaded file is not a valid PDF."""
    pass


class CorruptedPDFError(PDFServiceError):
    """Raised when the PDF file is corrupted and cannot be parsed."""
    pass


class EmptyFileError(PDFServiceError):
    """Raised when the uploaded file is empty (0 bytes)."""
    pass


class PDFService:
    """Service class for PDF operations."""

    @staticmethod
    def validate_pdf(file_bytes: bytes, filename: str) -> None:
        """Validate that the given bytes and filename represent a valid PDF.

        Args:
            file_bytes: Raw bytes of the uploaded file.
            filename: Original name of the uploaded file.

        Raises:
            EmptyFileError: If the file is 0 bytes.
            InvalidPDFError: If filename extension or header magic bytes are invalid.
        """
        if not filename or not filename.lower().endswith(".pdf"):
            raise InvalidPDFError("File must have a .pdf extension.")

        if not file_bytes or len(file_bytes) == 0:
            raise EmptyFileError("Uploaded file is empty (0 bytes).")

        # PDF files must start with %PDF- (standard magic bytes, allow leading whitespace)
        stripped_bytes = file_bytes.lstrip()
        if not stripped_bytes.startswith(b"%PDF-"):
            raise InvalidPDFError("File content does not match standard PDF header signature (%PDF-).")

    @classmethod
    def extract_text(cls, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Extract text from a PDF file using PyMuPDF.

        Args:
            file_bytes: Raw bytes of the uploaded file.
            filename: Original name of the uploaded file.

        Returns:
            Dict containing:
                - filename: str
                - total_pages: int
                - extracted_text: str
                - extraction_status: str ("success" or "empty")

        Raises:
            EmptyFileError: When file is 0 bytes.
            InvalidPDFError: When file format or header is invalid.
            CorruptedPDFError: When PDF cannot be opened or parsed.
        """
        cls.validate_pdf(file_bytes, filename)

        doc = None
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        except fitz.FileDataError as exc:
            raise CorruptedPDFError(f"Corrupted PDF file: unable to parse structure. ({str(exc)})") from exc
        except Exception as exc:
            raise CorruptedPDFError(f"Failed to open PDF document: {str(exc)}") from exc

        try:
            if doc.is_encrypted:
                # Try empty password for basic encrypted PDFs
                if not doc.authenticate(""):
                    raise InvalidPDFError("Encrypted or password-protected PDF files are not supported.")

            total_pages = doc.page_count
            if total_pages == 0:
                return {
                    "filename": filename,
                    "total_pages": 0,
                    "extracted_text": "",
                    "extraction_status": "empty",
                }

            page_texts = []
            for page_index in range(total_pages):
                page = doc.load_page(page_index)
                text = page.get_text("text")
                if text:
                    page_texts.append(text.strip())

            extracted_text = "\n\n".join(page_texts).strip()
            extraction_status = "success" if len(extracted_text) > 0 else "empty"

            return {
                "filename": filename,
                "total_pages": total_pages,
                "extracted_text": extracted_text,
                "extraction_status": extraction_status,
            }

        except (InvalidPDFError, CorruptedPDFError, EmptyFileError):
            raise
        except Exception as exc:
            raise CorruptedPDFError(f"Error extracting text from PDF: {str(exc)}") from exc
        finally:
            if doc is not None:
                doc.close()
