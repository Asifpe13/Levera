"""
Pydantic schemas for API request/response.

Security notes:
- All string fields have explicit max_length to prevent oversized payloads.
- Enum-like fields use Literal so invalid values are rejected at parse time.
- Email fields are normalised (lowercase + stripped) via field_validator.
- Free-text fields (extra_preferences) are stripped of HTML tags before storage.
- Numeric ranges are bounded to realistic domain values.
"""
import re
from typing import Optional, List, Literal, Annotated, Any

from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


def _strip_html(value: str) -> str:
    """Remove HTML/script tags from free-text user input."""
    return _HTML_TAG_RE.sub("", value).strip()


def _norm_email(raw: str) -> str:
    return (raw or "").strip().lower()


# ---------------------------------------------------------------------------
# Auth schemas
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: Annotated[str, Field(max_length=254)]
    # Passwords are bcrypt-hashed; cap at 128 chars (bcrypt silently truncates at 72 bytes,
    # so we keep passwords short enough to avoid silent truncation surprises on multi-byte chars).
    password: Annotated[str, Field(default="", max_length=128)]
    remember_me: bool = False

    @field_validator("email", mode="before")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return _norm_email(v)


class LoginResponse(BaseModel):
    email: str
    token: Optional[str] = None


class RegisterRequest(BaseModel):
    name: Annotated[str, Field(min_length=2, max_length=100)]
    email: Annotated[str, Field(max_length=254)]
    # min_length enforced in auth.py as well (belt-and-suspenders)
    password: Annotated[str, Field(default="", min_length=6, max_length=128)]

    # Financial
    equity: Annotated[int, Field(default=400_000, ge=0, le=50_000_000)]
    monthly_income: Annotated[int, Field(default=12_500, ge=0, le=5_000_000)]
    max_repayment_ratio: Annotated[float, Field(default=0.40, ge=0.1, le=0.6)]
    max_price: Optional[Annotated[int, Field(ge=0, le=500_000_000)]] = None
    max_rent: Optional[Annotated[int, Field(ge=0, le=1_000_000)]] = None

    # Cities (at most 30)
    target_cities: Annotated[List[str], Field(min_length=1, max_length=30)]

    # Search behaviour
    search_type: Literal["buy", "rent", "both"] = "both"
    profile_type: Literal["HOME_BUYER", "INVESTOR", "CASH_FLOW_MAXIMIZER"] = "HOME_BUYER"
    home_index: Annotated[int, Field(default=1, ge=1, le=3)]
    loan_term_years: Annotated[int, Field(default=30, ge=5, le=40)]

    # Room ranges
    room_range_min: Annotated[int, Field(default=3, ge=1, le=20)]
    room_range_max: Annotated[int, Field(default=5, ge=1, le=20)]
    rent_room_range_min: Annotated[int, Field(default=2, ge=1, le=20)]
    rent_room_range_max: Annotated[int, Field(default=5, ge=1, le=20)]

    # Free-text preferences — HTML stripped before storage
    extra_preferences: Optional[Annotated[str, Field(max_length=500)]] = None

    @field_validator("email", mode="before")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return _norm_email(v)

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return (v or "").strip()

    @field_validator("extra_preferences", mode="before")
    @classmethod
    def sanitise_preferences(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        cleaned = _strip_html(str(v))
        return cleaned or None

    @field_validator("target_cities", mode="before")
    @classmethod
    def validate_cities(cls, v: List[Any]) -> List[str]:
        if not v:
            raise ValueError("יש לבחור לפחות עיר אחת")
        # Coerce each item to str, limit individual city name length
        return [str(c).strip()[:100] for c in v[:30] if str(c).strip()]


# ---------------------------------------------------------------------------
# User schemas
# ---------------------------------------------------------------------------

class UserResponse(BaseModel):
    name: str
    email: str
    target_cities: List[str]
    search_type: str
    profile_type: str
    home_index: int
    loan_term_years: int
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
    name: Optional[Annotated[str, Field(min_length=2, max_length=100)]] = None
    target_cities: Optional[Annotated[List[str], Field(max_length=30)]] = None
    search_type: Optional[Literal["buy", "rent", "both"]] = None
    profile_type: Optional[Literal["HOME_BUYER", "INVESTOR", "CASH_FLOW_MAXIMIZER"]] = None
    home_index: Optional[Annotated[int, Field(ge=1, le=3)]] = None
    loan_term_years: Optional[Annotated[int, Field(ge=5, le=40)]] = None
    equity: Optional[Annotated[int, Field(ge=0, le=50_000_000)]] = None
    monthly_income: Optional[Annotated[int, Field(ge=0, le=5_000_000)]] = None
    room_range_min: Optional[Annotated[int, Field(ge=1, le=20)]] = None
    room_range_max: Optional[Annotated[int, Field(ge=1, le=20)]] = None
    max_price: Optional[Annotated[int, Field(ge=0, le=500_000_000)]] = None
    max_repayment_ratio: Optional[Annotated[float, Field(ge=0.1, le=0.6)]] = None
    rent_room_range_min: Optional[Annotated[int, Field(ge=1, le=20)]] = None
    rent_room_range_max: Optional[Annotated[int, Field(ge=1, le=20)]] = None
    max_rent: Optional[Annotated[int, Field(ge=0, le=1_000_000)]] = None
    extra_preferences: Optional[Annotated[str, Field(max_length=500)]] = None

    @field_validator("extra_preferences", mode="before")
    @classmethod
    def sanitise_preferences(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        cleaned = _strip_html(str(v))
        return cleaned or None

    @field_validator("target_cities", mode="before")
    @classmethod
    def validate_cities(cls, v: Optional[List[Any]]) -> Optional[List[str]]:
        if v is None:
            return None
        return [str(c).strip()[:100] for c in v[:30] if str(c).strip()]


def user_dict_to_response(d: dict) -> UserResponse:
    return UserResponse(
        name=d.get("name", ""),
        email=d.get("email", ""),
        target_cities=d.get("target_cities", []),
        search_type=d.get("search_type", "both"),
        profile_type=d.get("profile_type", "HOME_BUYER"),
        home_index=int(d.get("home_index", 1)),
        loan_term_years=int(d.get("loan_term_years", 30)),
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
    for key in ("found_at", "created_at", "updated_at"):
        if key in out and hasattr(out[key], "isoformat"):
            out[key] = out[key].isoformat()
    if "price_history" in out and out["price_history"]:
        out["price_history"] = [
            {
                "price": e.get("price"),
                "date": e.get("date").isoformat() if hasattr(e.get("date"), "isoformat") else e.get("date"),
            }
            for e in out["price_history"]
        ]
    return out
