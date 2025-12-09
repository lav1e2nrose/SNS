"""
Main FastAPI application entry point for SNS (Sentiment Analysis Chat).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from backend.app.core.config import settings
from backend.app.db.base import Base
from backend.app.db.session import engine
from backend.app.api.api_v1.api import api_router

# Import models to ensure they are registered with SQLAlchemy
from backend.app.models import user, message, friendship

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 router
app.include_router(api_router, prefix="/api/v1")

# Get the frontend directory path
FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend"


@app.get("/")
async def root():
    """Serve the frontend HTML page or return API info."""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/styles.css")
async def serve_css():
    """Serve the CSS file."""
    css_path = FRONTEND_DIR / "styles.css"
    if css_path.exists():
        return FileResponse(css_path, media_type="text/css")
    return {"error": "CSS file not found"}


@app.get("/app.js")
async def serve_js():
    """Serve the JavaScript file."""
    js_path = FRONTEND_DIR / "app.js"
    if js_path.exists():
        return FileResponse(js_path, media_type="application/javascript")
    return {"error": "JS file not found"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
