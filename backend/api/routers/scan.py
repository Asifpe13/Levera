"""Trigger scan for current user. Runs synchronously and returns log lines."""
import time

from fastapi import APIRouter, Depends

from api.deps import get_db, get_current_user_email
from database.db import DatabaseManager

router = APIRouter()


@router.post("")
def run_scan(
    email: str = Depends(get_current_user_email),
    db: DatabaseManager = Depends(get_db),
):
    """Run the scan for the current user. Returns list of log messages."""
    user = db.get_user_by_email(email)
    if not user:
        return {"ok": False, "log": [], "total_found": 0, "total_matches": 0}

    # Import here to avoid loading scrapers at app startup
    from engine import ScanEngine
    from logic import check_property_fit
    from config import build_listing_url
    from engine import _enrich_property_insights

    log_lines = []
    search_type = user.get("search_type", "both")
    cities = user.get("target_cities", [])
    deal_types = []
    if search_type in ("buy", "both", "sale"):
        deal_types.append("sale")
    if search_type in ("rent", "both"):
        deal_types.append("rent")

    def add_log(msg: str, level: str = "info"):
        t = time.strftime("%H:%M:%S")
        log_lines.append({"time": t, "level": level, "message": msg})

    add_log("🤖 הסוכן מתעורר ומתחיל סריקה...", "info")
    add_log(f"📋 פרמטרים: {', '.join(cities)} | {user.get('room_range_min', 3)}-{user.get('room_range_max', 5)} חדרים | {', '.join(deal_types)}", "info")

    engine = ScanEngine(db=db)
    total_found = 0
    total_matches = 0

    for dt in deal_types:
        add_log(f"🔄 סורק {'מכירה' if dt == 'sale' else 'שכירות'}...", "info")
        from scrapers.yad2_api_scraper import Yad2ApiScraper
        from scrapers.madlan_scraper import MadlanScraper
        from scrapers.homeless_scraper import HomelessScraper
        from scrapers.winwin_scraper import WinWinScraper
        scrapers = [
            ("Yad2", Yad2ApiScraper(deal_type=dt)),
            ("Madlan", MadlanScraper(deal_type=dt)),
            ("Homeless", HomelessScraper(deal_type=dt)),
            ("WinWin", WinWinScraper(deal_type=dt)),
        ]
        rooms_min = user.get("rent_room_range_min", 1) if dt == "rent" else user.get("room_range_min", 1)
        rooms_max = user.get("rent_room_range_max", 8) if dt == "rent" else user.get("room_range_max", 8)
        price_max = user.get("max_rent") if dt == "rent" else user.get("max_price")
        for scraper_name, scraper in scrapers:
            add_log(f"  → סורק {scraper_name}...", "info")
            try:
                results = scraper.search_all_cities(
                    cities=cities,
                    rooms_min=rooms_min,
                    rooms_max=rooms_max,
                    price_max=price_max,
                    max_pages=1,
                )
                if results:
                    add_log(f"  ✓ {scraper_name}: נמצאו {len(results)} דירות", "success")
                    total_found += len(results)
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
                    for prop_data in results:
                        if db.property_exists(prop_data.get("source", ""), prop_data.get("source_id", "")):
                            continue
                        fits, _ = check_property_fit(prop_data, prefs)
                        if not fits:
                            continue
                        analysis = engine.ai.analyze_property(prop_data, prefs)
                        prop_data["matched_user_email"] = email
                        prop_data["ai_score"] = analysis.get("score", 0)
                        prop_data["ai_summary"] = analysis.get("summary", "")
                        prop_data["monthly_repayment"] = analysis.get("monthly_repayment_estimate")
                        city_avg = db.get_avg_price_per_room_by_city(email)
                        _enrich_property_insights(prop_data, city_avg, engine.ai)
                        if not (prop_data.get("listing_url") or "").strip():
                            prop_data["listing_url"] = build_listing_url(
                                prop_data.get("source"), prop_data.get("source_id"), prop_data.get("deal_type")
                            )
                        try:
                            db.add_property(prop_data)
                            total_matches += 1
                            add_log(f"  🏠 נשמרה: {prop_data.get('city', '?')} | {prop_data.get('rooms', '?')} חד' | {prop_data.get('price', 0):,.0f}₪ | ציון {analysis.get('score', 0)}", "success")
                        except Exception:
                            pass
                else:
                    add_log(f"  — {scraper_name}: אין תוצאות", "warn")
            except Exception as e:
                add_log(f"  ✗ {scraper_name}: שגיאה - {str(e)[:60]}", "error")

    add_log(f"📊 בסריקה זו: נסרקו {total_found} דירות, נשמרו {total_matches} התאמות חדשות", "info")
    add_log("💤 הסוכן חוזר לישון.", "info")
    return {"ok": True, "log": log_lines, "total_found": total_found, "total_matches": total_matches}


@router.post("/weekly-report")
def trigger_weekly_report(
    email: str = Depends(get_current_user_email),
    db: DatabaseManager = Depends(get_db),
):
    """Generate and send the weekly report now for the current user (same as Thursday 21:00 job)."""
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
        props_before = db.get_weekly_properties(email, days=7)
        count = len(props_before)
        if count == 0:
            return {"ok": True, "message": "אין דירות להכליל השבוע. הדוח האוטומטי נשלח כל חמישי ב־21:00.", "properties_count": 0}
        engine._send_weekly_report_for_user(user)
        return {"ok": True, "message": "הדוח השבועי נשלח למייל", "properties_count": count}
    except Exception as e:
        return {"ok": False, "message": str(e)[:200], "properties_count": 0}
