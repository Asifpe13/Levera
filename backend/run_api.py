"""
הרצת ה-Backend (FastAPI).
הרץ מהשורש של הפרויקט: python run_api.py
"""
import os
import sys
from pathlib import Path

# backend root (run from repo root or from backend/)
ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# allow .env in repo root
from dotenv import load_dotenv
load_dotenv(ROOT.parent / ".env")
load_dotenv(ROOT / ".env")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
