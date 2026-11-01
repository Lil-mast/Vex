"""Vex FastAPI application."""

import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.exceptions import VexError
from app.models import ErrorResponse, HealthResponse
from app.routers import zones, countries, events, snapshots, quality, dates

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Vex API",
    description="Ebola Bundibugyo Outbreak Atlas — Apache Iceberg + Athena backend",
    version="0.1.0",
    openapi_url="/docs/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(VexError)
async def vex_exception_handler(request: Request, exc: VexError):
    """Handle custom Vex exceptions."""
    logger.error(f"Vex error: {exc.message}", exc_info=True)
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.__class__.__name__,
            detail=exc.message
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalServerError",
            detail="An unexpected error occurred"
        ).model_dump()
    )


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(status="ok")


# Include all routers
app.include_router(zones.router)
app.include_router(countries.router)
app.include_router(events.router)
app.include_router(snapshots.router)
app.include_router(quality.router)
app.include_router(dates.router)

logger.info("Vex API initialized with all routers")
