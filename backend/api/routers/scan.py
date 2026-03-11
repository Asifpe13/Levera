"""
Scan router.

POST /scan        → returns {"status": "started"} immediately;
                   actual scan runs as a FastAPI BackgroundTask.
GET  /scan/status → returns the current Hebrew progress message for
                   the authenticated user (polled every 2 s by the UI).
POST /scan/weekly-report → generate + send the weekly report now.
"""
import threading
import time
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends

from api.deps import get_current_user_email, get_db
from database.db import DatabaseManager

router = APIRouter()

# ---------------------------------------------------------------------------
# In-memory per-user scan state
# (works fine for single-worker deployments; extend to Redis for multi-worker)
# ---------------------------------------------------------------------------

_scan_states: dict[str, dict[str, Any]] = {}
_scan_lock = threading.Lock()


def _set_status(
    email: str,
    message: str,
    *,
    running: bool = True,
    finished: bool = False,
    total_found: int = 0,
    total_matches: int = 0,
    log: list[dict] | None = None,
) -> None:
    with _scan_lock:
        prev = _scan_states.get(email, {})
        _scan_states[email] = {
            "running": running,
            "message": message,
            "finished": finished,
            "total_found": total_found,
            "total_matches": total_matches,
            "log": log if log is not None else prev.get("log", []),
        }


def _append_log(email: str, msg: str, level: str = "info") -> None:
    t = time.strftime("%H:%M:%S")
    with _scan_lock:
        state = _scan_states.setdefault(email, {})
        state.setdefault("log", []).append({"time": t, "level": level, "message": msg})


# ---------------------------------------------------------------------------
# Background scan task
# ---------------------------------------------------------------------------

def _run_scan_bg(email: str, db: DatabaseManager) -> None:
    """Full scan logic — runs after the HTTP response is already returned."""
    from config import build_listing_url
    from engine import ScanEngine, _enrich_property_insights
    from logic import check_property_fit
    from scrapers.homeless_scraper import HomelessScraper
    from scrapers.madlan_scraper import MadlanScraper
    from scrapers.winwin_scraper import WinWinScraper
    from scrapers.yad2_api_scraper import Yad2ApiScraper

    total_found = 0
    total_matches = 0

    def log(msg: str, level: str = "info") -> None:
        _append_log(email, msg, level)
        _set_status(email, msg, running=True, total_found=total_found, total_matches=total_matches)

    try:
        user = db.get_user_by_email(email)
        if not user:
            _set_status(email, "משתמש לא נמצא", running=False, finished=True)
            return

        cities: list[str] = user.get("target_cities", [])
        search_type: str = user.get("search_type", "both")

        deal_types: list[str] = []
        if search_type in ("buy", "both", "sale"):
            deal_types.append("sale")
        if search_type in ("rent", "both"):
            deal_types.append("rent")

        log("🤖 הסוכן מתעורר ומתחיל סריקה...")
        log(
            f"📋 פרמטרים: {', '.join(cities)} | "
            f"{user.get('room_range_min', 3)}–{user.get('room_range_max', 5)} חדרים | "
            f"{', '.join(deal_types)}"
        )

        engine = ScanEngine(db=db)

        for dt in deal_types:
            label = "מכירה" if dt == "sale" else "שכירות"
            log(f"🔄 סורק {label}...")

            scrapers = [
                ("Yad2", Yad2ApiScraper(deal_type=dt)),
                ("Madlan", MadlanScraper(deal_type=dt)),
                ("Homeless", HomelessScraper(deal_type=dt)),
                ("WinWin", WinWinScraper(deal_type=dt)),
            ]
            rooms_min = user.get("rent_room_range_min", 1) if dt == "rent" else user.get("room_range_min", 1)
            rooms_max = user.get("rent_room_range_max", 8) if dt == "rent" else user.get("room_range_max", 8)
            price_max = user.get("max_rent") if dt == "rent" else user.get("max_price")

            prefs = {
                "target_cities": cities,
                "equity": user.get("equity", 0),
                "monthly_income": user.get("monthly_income", 0),
                "room_range_min": user.get("room_range_min", 1),
                "room_range_max": user.get("room_range_max", 8),
                "max_price": user.get("max_price"),
                "max_repayment_ratio": user.get("max_repayment_ratio", 0.4),
                "rent_room_range_min": user.get("rent_room_range_min", 1),
                "rent_room_range_max": user.get("rent_room_range_max", 8),
                "max_rent": user.get("max_rent"),
                "extra_preferences": user.get("extra_preferences"),
            }

            for scraper_name, scraper in scrapers:
                log(f"  → סורק {scraper_name}...")
                try:
                    # Per-city status so mobile users see live progress
                    for city in cities:
                        log(f"  🔍 סורק את {city} ב‑{scraper_name}...")
                    results = scraper.search_all_cities(
                        cities=cities,
                        rooms_min=rooms_min,
                        rooms_max=rooms_max,
                        price_max=price_max,
                        max_pages=1,
                    )
                    if results:
                        log(f"  ✓ {scraper_name}: נמצאו {len(results)} דירות", "success")
                        total_found += len(results)
                        for prop_data in results:
                            if db.property_exists(
                                prop_data.get("source", ""), prop_data.get("source_id", "")
                            ):
                                continue
                            fits, _ = check_property_fit(prop_data, prefs)
                            if not fits:
                                continue
                            log("  🧠 מנתח עם AI...")
                            analysis = engine.ai.analyze_property(prop_data, prefs)
                            prop_data["matched_user_email"] = email
                            prop_data["ai_score"] = analysis.get("score", 0)
                            prop_data["ai_summary"] = analysis.get("summary", "")
                            prop_data["monthly_repayment"] = analysis.get("monthly_repayment_estimate")
                            city_avg = db.get_avg_price_per_room_by_city(email)
                            _enrich_property_insights(prop_data, city_avg, engine.ai)
                            if not (prop_data.get("listing_url") or "").strip():
                                prop_data["listing_url"] = build_listing_url(
                                    prop_data.get("source"),
                                    prop_data.get("source_id"),
                                    prop_data.get("deal_type"),
                                )
                            try:
                                db.add_property(prop_data)
                                total_matches += 1
                                log(
                                    f"  🏠 נשמרה: {prop_data.get('city', '?')} | "
                                    f"{prop_data.get('rooms', '?')} חד׳ | "
                                    f"{prop_data.get('price', 0):,.0f}₪ | "
                                    f"ציון {analysis.get('score', 0)}",
                                    "success",
                                )
                            except Exception:
                                pass
                    else:
                        log(f"  — {scraper_name}: אין תוצאות", "warn")
                except Exception as e:
                    log(f"  ✗ {scraper_name}: שגיאה — {str(e)[:60]}", "error")

        summary = (
            f"📊 בסריקה זו: נסרקו {total_found} דירות, נשמרו {total_matches} התאמות חדשות"
        )
        log(summary)
        _append_log(email, "💤 הסוכן חוזר לישון.", "info")

    except Exception as e:
        _append_log(email, f"❌ שגיאה כללית: {str(e)[:120]}", "error")
    finally:
        with _scan_lock:
            state = _scan_states.setdefault(email, {})
            state["running"] = False
            state["finished"] = True
            state["total_found"] = total_found
            state["total_matches"] = total_matches
            state["message"] = f"הסריקה הושלמה — נמצאו {total_found} דירות, {total_matches} התאמות"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("")
def run_scan(
    background_tasks: BackgroundTasks,
    email: str = Depends(get_current_user_email),
    db: DatabaseManager = Depends(get_db),
):
    """Start a background scan and return immediately so mobile clients don't time out."""
    with _scan_lock:
        current = _scan_states.get(email, {})
        if current.get("running"):
            return {"status": "already_running"}

    _set_status(email, "מתחיל סריקה...", running=True, finished=False, log=[])
    background_tasks.add_task(_run_scan_bg, email, db)
    return {"status": "started"}


@router.get("/status")
def get_scan_status(email: str = Depends(get_current_user_email)):
    """Poll this endpoint every 2 s to get live Hebrew progress messages."""
    with _scan_lock:
        state = _scan_states.get(
            email,
            {
                "running": False,
                "message": "לא פעיל",
                "finished": False,
                "total_found": 0,
                "total_matches": 0,
                "log": [],
            },
        )
        return dict(state)


@router.post("/weekly-report")
def trigger_weekly_report(
    email: str = Depends(get_current_user_email),
    db: DatabaseManager = Depends(get_db),
):
    """Generate and send the weekly report immediately (same as Thursday 21:00 job)."""
    user = db.get_user_by_email(email)
    if not user:
        return {"ok": False, "message": "משתמש לא נמצא", "properties_count": 0}

    from engine import ScanEngine
    from services.ai_service import AIService
    from services.email_service import EmailService

    ai = AIService()
    email_svc = EmailService()
    engine = ScanEngine(db=db, ai=ai, email=email_svc)

    try:
        count = len(db.get_weekly_properties(email, days=7))
        if count == 0:
            return {
                "ok": True,
                "message": "אין דירות להכליל השבוע. הדוח האוטומטי נשלח כל חמישי ב‑21:00.",
                "properties_count": 0,
            }
        engine._send_weekly_report_for_user(user)
        return {"ok": True, "message": "הדוח השבועי נשלח למייל", "properties_count": count}
    except Exception as e:
        return {"ok": False, "message": str(e)[:200], "properties_count": 0}
