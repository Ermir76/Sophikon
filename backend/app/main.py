from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine


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


# Configure CORS
# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to Sophikon!"}
