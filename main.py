"""
IconScout Bot - Main Application
FastAPI server with automatic asset downloader.
"""
import logging
import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from config import config
from database import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("iconscout")

# Create FastAPI app
app = FastAPI(
    title="IconScout Bot",
    description="Automatic IconScout asset downloader with dashboard",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Startup / Shutdown ---

@app.on_event("startup")
async def startup():
    """Initialize database, scheduler, and services on startup."""
    logger.info("🚀 Starting IconScout Bot...")

    # Ensure directories exist
    config.DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    Path("data").mkdir(parents=True, exist_ok=True)

    # Initialize database
    await init_db()
    logger.info("✅ Database initialized")

    # Start scheduler
    from services.scheduler import scheduler_service
    await scheduler_service.start()
    logger.info("✅ Scheduler started")

    # Initialize cloud service if enabled
    if config.GOOGLE_DRIVE_ENABLED:
        from services.cloud_upload import cloud_service
        await cloud_service.initialize()
        logger.info("✅ Google Drive service initialized")

    logger.info(f"🌐 Server running at http://localhost:{config.PORT}")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    logger.info("Shutting down IconScout Bot...")

    from services.scheduler import scheduler_service
    await scheduler_service.stop()

    from services.iconscout_browser import browser_manager
    await browser_manager.close_all()

    from services.iconscout_api import iconscout_api
    await iconscout_api.close()

    logger.info("Shutdown complete")


# --- Register Routes ---

from routes.accounts import router as accounts_router
from routes.tasks import router as tasks_router
from routes.scheduler import router as scheduler_router
from routes.dashboard import router as dashboard_router
from routes.logs import router as logs_router

app.include_router(accounts_router)
app.include_router(tasks_router)
app.include_router(scheduler_router)
app.include_router(dashboard_router)
app.include_router(logs_router)


# --- Static Files & SPA ---

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def serve_index():
    """Serve the main dashboard page."""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "IconScout Bot API is running. Dashboard not found at /static/index.html"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}


# --- Run ---

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
    )
