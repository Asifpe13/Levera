"""Pydantic schemas for API request/response."""
from typing import Optional, List, Any
from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    remember_me: bool = False


class LoginResponse(BaseModel):
    email: str
    token: Optional[str] = None  # only if remember_me


class RegisterRequest(BaseModel):
    name: str
    email: str
    equity: int = 400_000
    monthly_income: int = 12_500
    max_repayment_ratio: float = 0.40
    target_cities: List[str]
    search_type: str = "both"  # buy, rent, both
    room_range_min: int = 3
    room_range_max: int = 5
    max_price: Optional[int] = None
    rent_room_range_min: int = 2
    rent_room_range_max: int = 5
    max_rent: Optional[int] = None
    extra_preferences: Optional[str] = None


class UserResponse(BaseModel):
    name: str
    email: str
    target_cities: List[str]
    search_type: str
    equity: float
    monthly_income: float
    room_range_min: int
    room_range_max: int
    max_price: Optional[float]
    max_repayment_ratio: float
    rent_room_range_min: int
    rent_room_range_max: int
    max_rent: Optional[float]
    extra_preferences: Optional[str]

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    target_cities: Optional[List[str]] = None
    search_type: Optional[str] = None
    equity: Optional[int] = None
    monthly_income: Optional[int] = None
    room_range_min: Optional[int] = None
    room_range_max: Optional[int] = None
    max_price: Optional[int] = None
    max_repayment_ratio: Optional[float] = None
    rent_room_range_min: Optional[int] = None
    rent_room_range_max: Optional[int] = None
    max_rent: Optional[int] = None
    extra_preferences: Optional[str] = None


def user_dict_to_response(d: dict) -> UserResponse:
    return UserResponse(
        name=d.get("name", ""),
        email=d.get("email", ""),
        target_cities=d.get("target_cities", []),
        search_type=d.get("search_type", "both"),
        equity=float(d.get("equity", 0)),
        monthly_income=float(d.get("monthly_income", 0)),
        room_range_min=int(d.get("room_range_min", 1)),
        room_range_max=int(d.get("room_range_max", 8)),
        max_price=d.get("max_price"),
        max_repayment_ratio=float(d.get("max_repayment_ratio", 0.4)),
        rent_room_range_min=int(d.get("rent_room_range_min", 1)),
        rent_room_range_max=int(d.get("rent_room_range_max", 8)),
        max_rent=d.get("max_rent"),
        extra_preferences=d.get("extra_preferences"),
    )


def serialize_property(p: dict) -> dict:
    """Convert MongoDB doc to JSON-safe dict (e.g. _id -> id)."""
    out = {k: v for k, v in p.items() if k != "_id"}
    if "_id" in p:
        out["id"] = str(p["_id"])
    # dates to isoformat if present
    for key in ("found_at", "created_at", "updated_at"):
        if key in out and hasattr(out[key], "isoformat"):
            out[key] = out[key].isoformat()
    if "price_history" in out and out["price_history"]:
        out["price_history"] = [
            {"price": e.get("price"), "date": e.get("date").isoformat() if hasattr(e.get("date"), "isoformat") else e.get("date")}
            for e in out["price_history"]
        ]
    return out
