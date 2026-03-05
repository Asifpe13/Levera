"""Auth: login, register. Returns token for remember_me."""
import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends

from api.deps import get_db
from api.schemas import LoginRequest, LoginResponse, RegisterRequest, user_dict_to_response
from database.db import DatabaseManager

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: DatabaseManager = Depends(get_db)):
    email = (body.email or "").strip()
    if not email:
        return LoginResponse(email="")
    user = db.get_user_by_email(email)
    if not user:
        return LoginResponse(email=email)  # frontend shows "no account"
    token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + (timedelta(days=7) if body.remember_me else timedelta(days=1))
    db.create_remember_token(token, email, expires_at)
    return LoginResponse(email=email, token=token)


@router.post("/register", response_model=LoginResponse)
def register(body: RegisterRequest, db: DatabaseManager = Depends(get_db)):
    email = (body.email or "").strip()
    if not email or not (body.name or "").strip():
        return LoginResponse(email=email or "")
    if not body.target_cities:
        return LoginResponse(email=email)
    db.upsert_user({
        "name": body.name.strip(),
        "email": email,
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
    })
    token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    db.create_remember_token(token, email, expires_at)
    return LoginResponse(email=email, token=token)


@router.get("/me")
def me(email: str = Depends(lambda: None)):
    """Current user info — use dependency get_current_user_email in real route."""
    pass
