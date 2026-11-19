from fastapi import APIRouter
from models.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint to verify backend service status."""
    return HealthResponse(
        status="healthy",
        service="VERITAS AI Backend",
        version="0.1.0",
    )
