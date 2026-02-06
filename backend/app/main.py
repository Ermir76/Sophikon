from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings


# Initialize the FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
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
