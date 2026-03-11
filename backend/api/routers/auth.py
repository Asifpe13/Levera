"""
Auth: register and login.

Passwords are hashed with bcrypt via passlib.
Legacy accounts (no password_hash) can still log in without a password
so that existing users aren't locked out after the upgrade.
"""
import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext

from api.deps import get_db
from api.schemas import LoginRequest, LoginResponse, RegisterRequest, user_dict_to_response
from database.db import DatabaseManager

router = APIRouter()

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _hash(password: str) -> str:
    return _pwd.hash(password)


def _verify(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: DatabaseManager = Depends(get_db)):
    email = (body.email or "").strip().lower()
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="נדרשת כתובת אימייל")

    user = db.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="לא נמצא חשבון עם אימייל זה — צור חשבון חדש",
        )

    stored_hash = user.get("password_hash")
    if stored_hash:
        # Account has a password — verify it
        if not body.password or not _verify(body.password, stored_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="סיסמה שגויה",
            )
    # Legacy accounts (no password_hash) bypass password check for backward compat

    token = str(uuid.uuid4())
    expires_at = (
        datetime.now(timezone.utc) + (timedelta(days=7) if body.remember_me else timedelta(days=1))
    )
    db.create_remember_token(token, email, expires_at)
    return LoginResponse(email=email, token=token)


@router.post("/register", response_model=LoginResponse)
def register(body: RegisterRequest, db: DatabaseManager = Depends(get_db)):
    email = (body.email or "").strip().lower()
    name = (body.name or "").strip()

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
