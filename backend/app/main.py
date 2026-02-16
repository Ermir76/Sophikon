from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.organizations import router as orgs_router
from app.api.v1.endpoints.organization_members import router as org_members_router
from app.api.v1.endpoints.projects import router as projects_router
from app.api.v1.endpoints.tasks import router as tasks_router
from app.api.v1.endpoints.resources import router as resources_router
from app.api.v1.endpoints.dependencies import router as dependencies_router
from app.api.v1.endpoints.assignments import (
    task_assignments_router,
    assignments_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage application lifecycle.

    Startup: Resources are ready (DB pool already created by engine)
    Shutdown: Close database connections gracefully
    """
    # Startup - engine pool is already created on import
    yield
    # Shutdown - dispose of connection pool
    await engine.dispose()


# Initialize the FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler to catch unhandled exceptions.

    Logs the full stack trace and returns a generic 500 error to the client
    to prevent leaking sensitive information.
    """
    logging.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )


# Configure CORS
# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(orgs_router, prefix="/api/v1")
app.include_router(org_members_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(resources_router, prefix="/api/v1")
app.include_router(dependencies_router, prefix="/api/v1")
app.include_router(task_assignments_router, prefix="/api/v1")
app.include_router(assignments_router, prefix="/api/v1")


# Health check endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to Sophikon!"}
