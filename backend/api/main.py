"""
FastAPI backend for Levera — Real Estate Decision Intelligence.
Run with: uvicorn api.main:app --reload --port 8000
"""
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Backend root (api/main.py -> parent.parent = backend)
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.chdir(ROOT)
from dotenv import load_dotenv
load_dotenv(ROOT.parent / ".env")  # repo root .env
load_dotenv(ROOT / ".env")

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from api.routers import auth, user, properties, scan, market, config as config_router, notifications


# ---------------------------------------------------------------------------
# Application lifespan — starts/stops the background scheduler
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the scheduler on startup and shut it down cleanly on exit."""
    try:
        from database.db import DatabaseManager
        from engine import ScanEngine
        from services.scheduler_service import SchedulerService

        db = DatabaseManager()
        engine = ScanEngine(db=db)
        scheduler = SchedulerService()

        # Hourly scan for all active users
        scheduler.add_scan_job(engine.run_scan_for_all_users)

        # Weekly report every Thursday at 21:00 Israel time
        scheduler.add_weekly_report_job(engine.send_weekly_reports)

        scheduler.start()
        logger.info("✅ Scheduler started: hourly scan + Thursday 21:00 weekly report")
    except Exception as exc:
        logger.error(f"❌ Scheduler failed to start: {exc}")
        scheduler = None  # type: ignore[assignment]

    yield  # application is running

    # Shutdown
    try:
        if scheduler and scheduler.scheduler.running:
            scheduler.stop()
            logger.info("Scheduler stopped cleanly")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Levera API",
    description="Backend for Levera dashboard — auth, properties, scan, market trends",
    version="1.0.0",
    redirect_slashes=False,   # prevent 307 redirects on trailing-slash mismatches
    lifespan=lifespan,
)

# CORS: local dev + any Vercel deployment (*.vercel.app) + optional CORS_ORIGINS
_cors_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8081",
    "http://127.0.0.1:8081",
    "http://localhost:19006",
    "http://127.0.0.1:19006",
    "capacitor://localhost",
    "http://localhost",
    "https://levera-pro.vercel.app",   # production frontend (exact origin)
    "https://levera-frontend-4k9gszksc-asifpe13s-projects.vercel.app",
]
_extra = os.getenv("CORS_ORIGINS", "").strip()
if _extra:
    _cors_origins.extend(s.strip() for s in _extra.split(",") if s.strip())

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",  # any Vercel preview/branch deploy
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all for unhandled exceptions.
    Returning a JSONResponse here ensures CORSMiddleware still wraps the response
    so the Access-Control-Allow-Origin header always reaches the browser.
    """
    import traceback
    logger.error(
        f"Unhandled error on {request.method} {request.url}: {exc}\n"
        f"{traceback.format_exc()}"
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "שגיאת שרת פנימית — נסה שוב מאוחר יותר"},
    )


app.include_router(auth.router,            prefix="/auth",       tags=["auth"])
app.include_router(user.router,            prefix="/user",       tags=["user"])
app.include_router(notifications.router,   prefix="/notifications", tags=["notifications"])
app.include_router(properties.router,      prefix="/properties", tags=["properties"])
app.include_router(scan.router,            prefix="/scan",       tags=["scan"])
app.include_router(market.router,          prefix="/market",     tags=["market"])
app.include_router(config_router.router,   prefix="/config",     tags=["config"])


@app.get("/")
def root():
    """Root endpoint for health checks and keep-alive pings (GitHub Actions). Returns 200 OK."""
    return {"message": "Levera API", "docs": "/docs", "health": "/health"}


@app.get("/health")
def health():
    return {"status": "ok"}
