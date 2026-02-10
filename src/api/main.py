"""
Gujarat Police SLM - FastAPI Application

Main entry point for the API server.
Wires together all route modules and middleware.
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.database import init_db, close_db
from src.api.routes import (
    auth_routes,
    sop_routes,
    chargesheet_routes,
    search_routes,
    utils_routes,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""
    logger.info("=" * 60)
    logger.info("Starting Gujarat Police SLM API...")
    logger.info("=" * 60)

    try:
        # Initialize database
        await init_db()
        logger.info("[OK] Database initialized")

        # Initialize RAG pipeline (lazy-loaded on first use via dependency)
        logger.info("[OK] RAG pipeline configured (lazy-load)")

        logger.info("=" * 60)
        logger.info("API server ready")
        logger.info("Docs: http://localhost:8000/docs")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise

    yield

    logger.info("Shutting down Gujarat Police SLM API...")
    await close_db()
    logger.info("Shutdown complete")


app = FastAPI(
    title="Gujarat Police AI Investigation Support System",
    description="RAG + Fine-tuned SLM for investigation support, chargesheet review, and case search",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ============================================
# CORS Middleware
# ============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# Request Timing Middleware
# ============================================
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header to all responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    return response


# ============================================
# Audit Logging Middleware
# ============================================
@app.middleware("http")
async def audit_log_middleware(request: Request, call_next):
    """Log all requests for audit trail."""
    start_time = time.time()

    # Get response
    response = await call_next(request)

    # Calculate duration
    duration_ms = int((time.time() - start_time) * 1000)

    # Log request
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Duration: {duration_ms}ms"
    )

    # TODO: Write to audit_log table (would need async DB session here)

    return response


# ============================================
# Error Handlers
# ============================================
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with proper JSON response."""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed feedback."""
    logger.warning(f"Validation error: {exc.errors()}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "detail": exc.errors(),
            "status_code": 422,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "status_code": 500,
        },
    )


# ============================================
# Include Routers
# ============================================
app.include_router(auth_routes.router)
app.include_router(sop_routes.router)
app.include_router(chargesheet_routes.router)
app.include_router(search_routes.router)
app.include_router(utils_routes.router)


# ============================================
# Root Endpoints
# ============================================
@app.get("/")
async def root():
    """API root - welcome message with endpoint listing."""
    return {
        "service": "Gujarat Police AI Investigation Support System",
        "version": "0.1.0",
        "status": "operational",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/utils/health",
            "auth": {
                "login": "POST /auth/login",
                "refresh": "POST /auth/refresh",
                "me": "GET /auth/me",
            },
            "sop": {
                "suggest": "POST /sop/suggest",
            },
            "chargesheet": {
                "review": "POST /chargesheet/review",
            },
            "search": {
                "query": "POST /search/query",
                "similar": "POST /search/similar",
                "filters": "GET /search/filters",
            },
            "utils": {
                "convert_section": "GET /utils/convert-section/{section}",
                "health": "GET /utils/health",
            },
        },
        "message": "See /docs for interactive API documentation",
    }


@app.get("/health")
async def health_check():
    """Legacy health check (redirect to /utils/health)."""
    return {
        "status": "healthy",
        "service": "gujpol-slm-api",
        "version": "0.1.0",
        "message": "Use /utils/health for detailed health check"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
