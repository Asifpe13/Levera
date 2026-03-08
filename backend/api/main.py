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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import auth, user, properties, scan, market, config as config_router

app = FastAPI(
    title="Levera API",
    description="Backend for Levera dashboard — auth, properties, scan, market trends",
    version="1.0.0",
)

# CORS: allow local dev + Vercel frontend (and optional CORS_ORIGINS env)
_cors_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://levera-frontend-six.vercel.app",
    "https://levera-frontend-qtsfyd012-asifpe13s-projects.vercel.app",
]
_extra = os.getenv("CORS_ORIGINS", "").strip()
if _extra:
    _cors_origins.extend(s.strip() for s in _extra.split(",") if s.strip())
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(user.router, prefix="/user", tags=["user"])
app.include_router(properties.router, prefix="/properties", tags=["properties"])
app.include_router(scan.router, prefix="/scan", tags=["scan"])
app.include_router(market.router, prefix="/market", tags=["market"])
app.include_router(config_router.router, prefix="/config", tags=["config"])


@app.get("/")
def root():
    return {"message": "Levera API", "docs": "/docs", "health": "/health"}


@app.get("/health")
def health():
    return {"status": "ok"}
