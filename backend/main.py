"""VERITAS AI - Backend Application Entry Point

FastAPI server providing endpoints for document upload, text extraction,
and verification pipeline.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.health import router as health_router
from routes.upload import router as upload_router

app = FastAPI(
    title="VERITAS AI Backend",
    description="Backend API for document ingestion, verification, and text analysis.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
# Defaults allow Vite / React frontend running on localhost:5173
raw_cors = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
cors_origins = [origin.strip() for origin in raw_cors.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes under /api prefix
app.include_router(health_router, prefix="/api")
app.include_router(upload_router, prefix="/api")


@app.get("/", tags=["Root"])
async def root():
    """Root landing endpoint with system metadata and documentation link."""
    return {
        "name": "VERITAS AI Backend API",
        "version": "0.1.0",
        "status": "online",
        "documentation": "/docs",
        "endpoints": {
            "health": "/api/health",
            "upload": "/api/upload",
        },
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=True)
