"""FastAPI dependencies: DB and current user from token."""
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyQuery, HTTPBearer, HTTPAuthorizationCredentials

# Backend root
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent  # backend/
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.db import DatabaseManager

_db: Optional[DatabaseManager] = None


def get_db() -> DatabaseManager:
    global _db
    if _db is None:
        _db = DatabaseManager()
    return _db


# Token via query (e.g. ?token=...) or Bearer header
token_query = APIKeyQuery(name="token", auto_error=False)
bearer = HTTPBearer(auto_error=False)


async def get_current_user_email(
    db: DatabaseManager = Depends(get_db),
    token: Optional[str] = Depends(token_query),
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
) -> str:
    """Resolve email from token (query or Bearer). Raises 401 if invalid."""
    t = token or (creds.credentials if creds else None)
    if not t:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing token (query ?token= or Authorization: Bearer)",
        )
    email = db.get_email_by_remember_token(t)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user = db.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return email
