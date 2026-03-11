"""
FastAPI backend for Levera — Real Estate Decision Intelligence.
Run with: uvicorn api.main:app --reload --port 8000
"""
import os
import sys
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

from api.routers import auth, user, properties, scan, market, config as config_router

app = FastAPI(
    title="Levera API",
    description="Backend for Levera dashboard — auth, properties, scan, market trends",
    version="1.0.0",
    redirect_slashes=False,   # prevent 307 redirects on trailing-slash mismatches
)

# CORS: local dev + any Vercel deployment (*.vercel.app) + optional CORS_ORIGINS
_cors_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://levera-pro.vercel.app",   # production frontend (exact origin)
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
    Returning a JSONResponse here (rather than letting Starlette's ServerErrorMiddleware
    take over) ensures the CORSMiddleware still wraps the response and the
    Access-Control-Allow-Origin header reaches the browser.
    """
    import traceback
    from loguru import logger
    logger.error(f"Unhandled error on {request.method} {request.url}: {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"detail": "שגיאת שרת פנימית — נסה שוב מאוחר יותר"},
    )


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(user.router, prefix="/user", tags=["user"])
app.include_router(properties.router, prefix="/properties", tags=["properties"])
app.include_router(scan.router, prefix="/scan", tags=["scan"])
app.include_router(market.router, prefix="/market", tags=["market"])
app.include_router(config_router.router, prefix="/config", tags=["config"])


@app.get("/")
def root():
    """Root endpoint for health checks and keep-alive pings (e.g. GitHub Actions). Returns 200 OK."""
    return {"message": "Levera API", "docs": "/docs", "health": "/health"}


@app.get("/health")
def health():
    return {"status": "ok"}
