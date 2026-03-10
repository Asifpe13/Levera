"""Properties list for current user with optional filters."""
from typing import Optional, Literal

from fastapi import APIRouter, Depends, Query

from api.deps import get_db, get_current_user_email
from api.schemas import serialize_property
from database.db import DatabaseManager
from config import build_listing_url

router = APIRouter()


@router.get("/")
def list_properties(
    email: str = Depends(get_current_user_email),
    db: DatabaseManager = Depends(get_db),
    deal_type: Optional[str] = Query(None, description="sale | rent"),
    city: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    view: Optional[Literal["latest", "all"]] = Query(
        "all", description="'latest' = most recent scan only; 'all' = entire history"
    ),
):
    if view == "latest":
        raw = db.get_latest_scan_properties(email, limit=limit)
    else:
        raw = db.get_all_properties_for_user(email, limit=limit)

    if deal_type:
        want_rent = deal_type.lower() == "rent"
        raw = [p for p in raw if (p.get("deal_type") == "rent") == want_rent]
    if city:
        raw = [p for p in raw if (p.get("city") or "").strip() == city.strip()]

    for p in raw:
        if not (p.get("listing_url") or "").strip() and p.get("source") and p.get("source_id"):
            p["listing_url"] = build_listing_url(
                p.get("source"), p.get("source_id"), p.get("deal_type")
            )
    return [serialize_property(p) for p in raw]
