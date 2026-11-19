"""Main FastAPI application entry point for SUAMS."""
from typing import Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from suams.auth.router import router as auth_router
from suams.users.router import router as users_router
from suams.registration.router import router as registration_router
from suams.exams.router import router as exams_router
from suams.results.router import router as results_router
from suams.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Smart University Academic Management System API with strict RBAC, TDD, and Design Patterns.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include module routers under /api
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(registration_router, prefix=settings.API_V1_STR)
app.include_router(exams_router, prefix=settings.API_V1_STR)
app.include_router(results_router, prefix=settings.API_V1_STR)


@app.get("/")
def root() -> dict[str, Any]:
    """Root endpoint verifying API availability."""
    return {
        "project": settings.PROJECT_NAME,
        "status": "online",
        "docs": "/docs",
    }


@app.get("/api/health")
def health_check() -> dict[str, str]:
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}
