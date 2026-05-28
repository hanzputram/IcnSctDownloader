"""
IconScout Bot - Main Application
FastAPI server with automatic asset downloader.
"""
import asyncio
import logging
import sys
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
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
    """Initialize database, scheduler, proxy pool, and services on startup."""
    logger.info("[START] Starting IconScout Bot...")

    # Ensure directories exist
    config.DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    Path("data").mkdir(parents=True, exist_ok=True)

    # Initialize database
    await init_db()
    logger.info("[OK] Database initialized")

    # Start scheduler
    from services.scheduler import scheduler_service
    await scheduler_service.start()
    logger.info("[OK] Scheduler started")

    # Initialize proxy pool in background (non-blocking)
    async def _init_proxy_pool():
        try:
            from services.proxy_manager import proxy_manager
            stats = await proxy_manager.refresh_pool(validate=True)
            logger.info(f"[OK] Proxy pool initialized: {stats.get('alive', 0)} alive proxies")
        except Exception as e:
            logger.warning(f"[WARN] Proxy pool init failed (will retry later): {e}")

    asyncio.create_task(_init_proxy_pool())

    # Initialize cloud service if enabled
    if config.GOOGLE_DRIVE_ENABLED:
        from services.cloud_upload import cloud_service
        await cloud_service.initialize()
        logger.info("[OK] Google Drive service initialized")

    logger.info(f"[SERVER] Running at http://localhost:{config.PORT}")


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


# --- Register API Routes (MUST come before catch-all) ---

from routes.accounts import router as accounts_router
from routes.tasks import router as tasks_router
from routes.scheduler import router as scheduler_router
from routes.dashboard import router as dashboard_router
from routes.logs import router as logs_router
from routes.proxy import router as proxy_router

app.include_router(dashboard_router)
app.include_router(accounts_router)
app.include_router(tasks_router)
app.include_router(scheduler_router)
app.include_router(logs_router)
app.include_router(proxy_router)


# --- Health Check (before catch-all) ---

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}


# --- Static Files & SPA (catch-all MUST be LAST) ---

dist_dir = Path(__file__).parent / "static" / "dist"
(dist_dir / "assets").mkdir(parents=True, exist_ok=True)

# Mount Vite assets directory
app.mount("/assets", StaticFiles(directory=str(dist_dir / "assets")), name="assets")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve the main dashboard page and handle SPA routing."""
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API route not found")

    index_path = dist_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "IconScout Bot API is running. Vue SPA is not built yet."}


# --- Run ---

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
    )
