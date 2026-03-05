"""
Pydantic models for MongoDB document validation.
Each model maps to a MongoDB collection.
"""
from datetime import datetime, timezone
from typing import Optional, Any

from pydantic import BaseModel, Field


class User(BaseModel):
    name: str
    email: str
    target_cities: list[str] = []
    search_type: str = "both"  # "buy", "rent", "both"
    # פרופיל החלטה: קונה דירה ראשונה / משקיע / מקסום תזרים
    profile_type: str = "HOME_BUYER"  # "HOME_BUYER" | "INVESTOR" | "CASH_FLOW_MAXIMIZER"
    # אינדקס דירה ביחס למשתמש: 1=דירה ראשונה, 2=שנייה, 3=שלישית+
    home_index: int = 1
    extra_preferences: Optional[str] = None
    is_active: bool = True
    # ─── מכירה ───
    equity: float = 0
    monthly_income: float = 0
    room_range_min: int = 1
    room_range_max: int = 8
    max_price: Optional[float] = None
    max_repayment_ratio: float = 0.40
    # ─── שכירות (נפרד) ───
    rent_room_range_min: int = 1
    rent_room_range_max: int = 8
    max_rent: Optional[float] = None  # תקציב שכירות חודשי מקסימלי (₪)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Property(BaseModel):
    source: str
    source_id: Optional[str] = None
    deal_type: str = "sale"  # "sale" or "rent"
    title: Optional[str] = None
    city: str
    neighborhood: Optional[str] = None
    address: Optional[str] = None
    rooms: Optional[float] = None
    floor: Optional[int] = None
    total_floors: Optional[int] = None
    size_sqm: Optional[float] = None
    price: float
    description: Optional[str] = None
    image_url: Optional[str] = None
    listing_url: Optional[str] = None
    property_type: Optional[str] = None
    is_new: bool = False
    has_parking: Optional[bool] = None
    has_elevator: Optional[bool] = None
    has_balcony: Optional[bool] = None
    has_storage: Optional[bool] = None
    has_mamad: Optional[bool] = None
    raw_data: Optional[dict] = None

    matched_user_email: Optional[str] = None

    ai_score: Optional[float] = None
    ai_summary: Optional[str] = None
    monthly_repayment: Optional[float] = None
    loan_amount: Optional[float] = None  # סכום המשכנתא (מחיר − הון עצמי), לפי חוק המשכנתא

    # Price history & deal flags (SaaS)
    price_history: list[dict[str, Any]] = Field(default_factory=list)  # [{"price": float, "date": datetime}]
    price_drop: bool = False

    # Investor / value (SaaS)
    estimated_rent: Optional[float] = None
    annual_yield_pct: Optional[float] = None
    value_label: Optional[str] = None  # "Below Market Value" | "Fair Price" | "Overpriced"
    neighborhood_insights: Optional[str] = None

    # Market comparison (gov sales data via Gemini + Google Search)
    market_confidence: Optional[int] = None  # 0-100
    market_avg_per_sqm: Optional[float] = None
    price_deviation_pct: Optional[float] = None  # % above/below area average
    market_summary_text: Optional[str] = None  # e.g. "Similar properties sold for ₪X per SQM (Gov data)"
    # הודעת הקשר לפי פרופיל (Home Buyer / Investor / Cash Flow) שתציג "הוכחה מהשטח"
    profile_area_message: Optional[str] = None

    email_sent: bool = False
    included_in_report: bool = False

    found_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserSearch(BaseModel):
    user_email: str
    search_params: dict
    results_count: int = 0
    matches_count: int = 0
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WeeklyReport(BaseModel):
    user_email: str
    property_ids: list[str] = []
    total_properties: int = 0
    report_html: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
