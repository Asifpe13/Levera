"""
Auth: register and login.

Passwords are hashed directly with the bcrypt library (no passlib wrapper).
Legacy accounts (no password_hash) can still log in without a password
so that existing users aren't locked out after the upgrade.

Brute-force protection:
- Failed login attempts are tracked per email in an in-memory sliding-window counter.
- After _MAX_ATTEMPTS failures within _WINDOW_SECONDS the endpoint returns 429.
- A short sleep is injected on every failed attempt to slow down automated guessing
  even before the hard limit is reached.
"""
import threading
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone, timedelta

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status

from api.deps import get_db
from api.schemas import LoginRequest, LoginResponse, RegisterRequest, user_dict_to_response
from database.db import DatabaseManager

router = APIRouter()

# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Brute-force rate limiter  (in-memory, per email address)
# ---------------------------------------------------------------------------

_MAX_ATTEMPTS = 5        # maximum failures allowed inside the window
_WINDOW_SECONDS = 300    # rolling 5-minute window
_FAILURE_SLEEP = 1.0     # seconds to sleep after every failure (slows down bots)

_failed: dict[str, list[float]] = defaultdict(list)
_failed_lock = threading.Lock()


def _check_rate_limit(key: str) -> None:
    """Raise 429 if the key (email) has exceeded the failure threshold."""
    now = time.monotonic()
    with _failed_lock:
        recent = [t for t in _failed[key] if now - t < _WINDOW_SECONDS]
        _failed[key] = recent
        if len(recent) >= _MAX_ATTEMPTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="יותר מדי ניסיונות כושלים — נסה שוב עוד מספר דקות",
                headers={"Retry-After": str(_WINDOW_SECONDS)},
            )


def _record_failure(key: str) -> None:
    with _failed_lock:
        _failed[key].append(time.monotonic())


def _clear_failures(key: str) -> None:
    with _failed_lock:
        _failed.pop(key, None)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: DatabaseManager = Depends(get_db)):
    email = (body.email or "").strip().lower()
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="נדרשת כתובת אימייל")

    # Check rate limit before any DB call so we don't leak user-existence info
    _check_rate_limit(email)

    user = db.get_user_by_email(email)
    if not user:
        # Uniform delay: prevents timing-based user enumeration
        time.sleep(_FAILURE_SLEEP)
        _record_failure(email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="לא נמצא חשבון עם אימייל זה — צור חשבון חדש",
        )

    stored_hash = user.get("password_hash")
    if stored_hash:
        if not body.password or not _verify(body.password, stored_hash):
            time.sleep(_FAILURE_SLEEP)
            _record_failure(email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="סיסמה שגויה",
            )
    # Legacy accounts (no password_hash) bypass password check for backward compat

    _clear_failures(email)

    token = str(uuid.uuid4())
    expires_at = (
        datetime.now(timezone.utc) + (timedelta(days=7) if body.remember_me else timedelta(days=1))
    )
    db.create_remember_token(token, email, expires_at)
    return LoginResponse(email=email, token=token)


@router.post("/register", response_model=LoginResponse)
def register(body: RegisterRequest, db: DatabaseManager = Depends(get_db)):
    # Pydantic has already validated field lengths/types at this point.
    email = body.email  # already normalised by schema validator
    name = body.name    # already stripped

    # Belt-and-suspenders checks (Pydantic catches most, but belt keeps code clear)
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="נדרשת כתובת אימייל")
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="נדרש שם מלא")
    if not body.target_cities:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="יש לבחור לפחות עיר אחת")
    if not body.password or len(body.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="הסיסמה חייבת להכיל לפחות 6 תווים",
        )

    existing = db.get_user_by_email(email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="כתובת אימייל זו כבר רשומה במערכת — התחבר עם הסיסמה שלך",
        )

    db.upsert_user({
        "name": name,
        "email": email,
        "password_hash": _hash(body.password),
        "equity": body.equity,
        "monthly_income": body.monthly_income,
        "target_cities": body.target_cities,
        "room_range_min": body.room_range_min,
        "room_range_max": body.room_range_max,
        "max_price": body.max_price if body.max_price and body.max_price > 0 else None,
        "max_repayment_ratio": body.max_repayment_ratio,
        "rent_room_range_min": body.rent_room_range_min,
        "rent_room_range_max": body.rent_room_range_max,
        "max_rent": body.max_rent if body.max_rent and body.max_rent > 0 else None,
        "search_type": body.search_type,
        "extra_preferences": body.extra_preferences,
        "profile_type": body.profile_type,
        "home_index": body.home_index,
        "loan_term_years": body.loan_term_years,
    })

    token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    db.create_remember_token(token, email, expires_at)
    return LoginResponse(email=email, token=token)
