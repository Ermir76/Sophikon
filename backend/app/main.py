import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.endpoints.activity import router as activity_router
from app.api.v1.endpoints.ai import router as ai_router
from app.api.v1.endpoints.assignments import (
    assignments_router,
    task_assignments_router,
)
from app.api.v1.endpoints.attachments import router as attachments_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.calendars import router as calendars_router
from app.api.v1.endpoints.comments import router as comments_router
from app.api.v1.endpoints.dependencies import router as dependencies_router
from app.api.v1.endpoints.insights import router as insights_router
from app.api.v1.endpoints.notifications import router as notifications_router
from app.api.v1.endpoints.organization_members import router as org_members_router
from app.api.v1.endpoints.organizations import router as orgs_router
from app.api.v1.endpoints.project_members import router as project_members_router
from app.api.v1.endpoints.projects import router as projects_router
from app.api.v1.endpoints.resources import router as resources_router
from app.api.v1.endpoints.schedule import router as schedule_router
from app.api.v1.endpoints.tasks import router as tasks_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.utilization import router as utilization_router
from app.api.v1.endpoints.ws import router as ws_router
from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import AppException
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.core.storage import ensure_media_directories, get_media_root
from app.core.user_notification_websocket_manager import (
    user_notification_websocket_manager,
)
from app.core.websocket_manager import websocket_manager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """
    Manage application lifecycle.

    Startup: Resources are ready (DB pool already created by engine)
    Shutdown: Close database connections gracefully
    """
    # Startup - engine pool is already created on import
    await websocket_manager.start()
    await user_notification_websocket_manager.start()
    yield
    # Shutdown - dispose of connection pool
    await user_notification_websocket_manager.stop()
    await websocket_manager.stop()
    await engine.dispose()


# Initialize the FastAPI application
_is_dev = settings.ENV == "development"

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs" if _is_dev else None,
    redoc_url="/redoc" if _is_dev else None,
    openapi_url="/openapi.json" if _is_dev else None,
)

# Set up Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


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
        content={
            "error": {"code": "INTERNAL_ERROR", "message": "Internal Server Error"}
        },
    )


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handler for custom application exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.error_code, "message": exc.message}},
        headers=exc.headers,
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

# Serve locally uploaded media files (avatars).
ensure_media_directories()
media_root = get_media_root()
app.mount(
    settings.MEDIA_URL_PREFIX,
    StaticFiles(directory=str(media_root)),
    name="media",
)


# Register routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(orgs_router, prefix="/api/v1")
app.include_router(org_members_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(project_members_router, prefix="/api/v1")
app.include_router(activity_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(resources_router, prefix="/api/v1")
app.include_router(dependencies_router, prefix="/api/v1")
app.include_router(insights_router, prefix="/api/v1")
app.include_router(schedule_router, prefix="/api/v1")
app.include_router(utilization_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(calendars_router, prefix="/api/v1")
app.include_router(comments_router, prefix="/api/v1")
app.include_router(attachments_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(task_assignments_router, prefix="/api/v1")
app.include_router(assignments_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(ws_router, prefix="/api/v1")


# Health check endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to Sophikon!"}
