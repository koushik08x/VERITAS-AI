from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="healthy", description="Status of the API service")
    service: str = Field(default="VERITAS AI Backend", description="Service identifier")
    version: str = Field(default="0.1.0", description="Backend version")


class PDFExtractionResponse(BaseModel):
    filename: str = Field(..., description="Name of the uploaded PDF file")
    total_pages: int = Field(..., description="Total number of pages in the PDF")
    extracted_text: str = Field(..., description="Extracted text from the PDF document")
    extraction_status: str = Field(
        ...,
        description="Status of the extraction: 'success' when text extracted, 'empty' when no text present",
    )


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message description")
