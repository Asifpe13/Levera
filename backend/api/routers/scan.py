"""
Scan router.

POST /scan        → returns {"status": "started"} immediately;
                   actual scan runs as a FastAPI BackgroundTask.
GET  /scan/status → returns the current Hebrew progress message for
                   the authenticated user (polled every 2 s by the UI).
POST /scan/weekly-report → generate + send the weekly report now.

Performance features:
- Scrapers run in parallel threads (one per source site).
- Scraper results are cached for 10 minutes to avoid redundant HTTP calls.
- AI analysis is batched every 5 candidates so progress updates flow to the UI
  before the entire AI phase finishes.
"""
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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

# ---------------------------------------------------------------------------
# Scraper result cache (10-minute TTL, keyed by site+deal+cities+rooms+price)
# ---------------------------------------------------------------------------

_CACHE_TTL = 600  # seconds
_AI_BATCH_SIZE = 5

_scraper_cache: dict[str, tuple[float, list[dict]]] = {}
_cache_lock = threading.Lock()


def _cached_search(scraper, cities: list[str], rooms_min: int,
                   rooms_max: int, price_max: Any) -> list[dict]:
    """Run scraper.search_all_cities, returning a cached copy when fresh."""
    from loguru import logger
    key = (
        f"{scraper.SOURCE_NAME}:{scraper.deal_type}:"
        f"{':'.join(sorted(cities))}:{rooms_min}:{rooms_max}:{price_max}"
    )
    now = time.monotonic()
    with _cache_lock:
        if key in _scraper_cache:
            cached_at, cached_results = _scraper_cache[key]
            if now - cached_at < _CACHE_TTL:
                logger.debug(f"[cache] HIT {scraper.SOURCE_NAME}/{scraper.deal_type}")
                return list(cached_results)

    results = scraper.search_all_cities(
        cities=cities,
        rooms_min=rooms_min,
        rooms_max=rooms_max,
        price_max=price_max,
        max_pages=1,
    )

    with _cache_lock:
        # Simple eviction: drop entries older than TTL whenever cache grows large
        if len(_scraper_cache) > 500:
            stale = [k for k, (t, _) in _scraper_cache.items() if now - t >= _CACHE_TTL]
            for k in stale:
                del _scraper_cache[k]
        _scraper_cache[key] = (now, list(results))

    return results


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

def _classify_fit_rejection(reason: str) -> str:
    """Map a check_property_fit rejection reason string to a rejection bucket."""
    r = reason.lower()
    if any(k in r for k in ("החזר חודשי", "הון עצמי", "משכנתא", "הכנסה", "בנקים")):
        return "high_mortgage"
    if any(k in r for k in ("מחיר", "תקציב", "שכר דירה")):
        return "over_budget"
    if any(k in r for k in ("חדרים", "חדר")):
        return "wrong_rooms"
    return "other"


def _classify_ai_rejection(summary: str) -> str:
    """Classify a low-score AI summary into suspicious vs irrelevant."""
    s = summary.lower()
    if any(k in s for k in ("שותפ", "מחסן", "חדר", "חלק מדירה", "לא דירה", "לא מתאים", "סטודנט")):
        return "irrelevant"
    if any(k in s for k in ("חשוד", "לא אמין", "מפוקפק", "הונאה", "שגוי", "מחיר חריג", "מניפולציה")):
        return "suspicious"
    return "low_score"


def _run_scan_bg(email: str, db: DatabaseManager) -> None:
    """Full scan logic — runs after the HTTP response is already returned.

    Architecture:
      Phase 1  Scraping    — all 4 source sites run in parallel threads.
      Phase 2  Filtering   — deterministic check_property_fit per listing.
      Phase 3  AI batches  — AI analysis in groups of _AI_BATCH_SIZE so the
                             UI receives incremental progress messages.
    """
    print(f"DEBUG: Background scan task actually started for {email}", flush=True)
    from config import MIN_AI_SCORE_FOR_ALERT, build_listing_url
    from engine import ScanEngine, _enrich_property_insights
    from logic import check_property_fit
    from scrapers.homeless_scraper import HomelessScraper
    from scrapers.madlan_scraper import MadlanScraper
    from scrapers.winwin_scraper import WinWinScraper
    from scrapers.yad2_api_scraper import Yad2ApiScraper

    total_found = 0
    total_matches = 0
    rejections: dict[str, int] = {
        "high_mortgage": 0,
        "over_budget":   0,
        "wrong_rooms":   0,
        "suspicious":    0,
        "irrelevant":    0,
        "low_score":     0,
        "other":         0,
    }

    def log(msg: str, level: str = "info") -> None:
        _append_log(email, msg, level)
        with _scan_lock:
            state = _scan_states.setdefault(email, {})
            state["running"] = True
            state["message"] = msg
            state["total_found"] = total_found
            state["total_matches"] = total_matches
            state["rejections"] = dict(rejections)

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
        # Compute city price averages once — reused for every property enrichment
        city_avg = db.get_avg_price_per_room_by_city(email)

        for dt in deal_types:
            label = "מכירה" if dt == "sale" else "שכירות"
            log(f"🔄 סורק {label} במקביל בכל האתרים...")

            rooms_min = (
                user.get("rent_room_range_min", 1) if dt == "rent"
                else user.get("room_range_min", 1)
            )
            rooms_max = (
                user.get("rent_room_range_max", 8) if dt == "rent"
                else user.get("room_range_max", 8)
            )
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

            scrapers_list = [
                ("Yad2",    Yad2ApiScraper(deal_type=dt)),
                ("Madlan",  MadlanScraper(deal_type=dt)),
                ("Homeless", HomelessScraper(deal_type=dt)),
                ("WinWin",  WinWinScraper(deal_type=dt)),
            ]

            # ── Phase 1: parallel scraping ────────────────────────────────
            def _run_one_scraper(item: tuple) -> tuple[str, list[dict], str | None]:
                name, scraper = item
                try:
                    results = _cached_search(scraper, cities, rooms_min, rooms_max, price_max)
                    return name, results, None
                except Exception as exc:
                    return name, [], str(exc)

            all_raw: list[dict] = []
            with ThreadPoolExecutor(max_workers=4, thread_name_prefix="scraper") as pool:
                future_to_name = {
                    pool.submit(_run_one_scraper, item): item[0]
                    for item in scrapers_list
                }
                for future in as_completed(future_to_name):
                    name, results, err = future.result()
                    if err:
                        log(f"  ✗ {name}: שגיאה — {err[:60]}", "error")
                    elif results:
                        log(f"  ✓ {name}: נמצאו {len(results)} דירות", "success")
                        all_raw.extend(results)
                        total_found += len(results)
                    else:
                        log(f"  — {name}: אין תוצאות", "warn")

            # ── Phase 2: deterministic filtering ─────────────────────────
            candidates: list[dict] = []
            for prop_data in all_raw:
                if db.property_exists(
                    prop_data.get("source", ""), prop_data.get("source_id", "")
                ):
                    continue
                fits, reason = check_property_fit(prop_data, prefs)
                if not fits:
                    bucket = _classify_fit_rejection(str(reason))
                    rejections[bucket] = rejections.get(bucket, 0) + 1
                else:
                    candidates.append(prop_data)

            if candidates:
                log(f"📋 {len(candidates)} מועמדים עוברים לניתוח AI (מתוך {total_found} שנסרקו)")
            else:
                log(f"📋 אין מועמדים לניתוח AI לאחר סינון (נסרקו {total_found} דירות)", "warn")

            # ── Phase 3: AI analysis in batches ───────────────────────────
            for batch_start in range(0, len(candidates), _AI_BATCH_SIZE):
                batch = candidates[batch_start: batch_start + _AI_BATCH_SIZE]
                batch_end = min(batch_start + _AI_BATCH_SIZE, len(candidates))
                log(f"  🧠 AI: מנתח דירות {batch_start + 1}–{batch_end} מתוך {len(candidates)}...")

                for prop_data in batch:
                    analysis = engine.ai.analyze_property(prop_data, prefs)
                    ai_score = analysis.get("score", 0)
                    ai_summary = analysis.get("summary", "")

                    if ai_score < MIN_AI_SCORE_FOR_ALERT:
                        bucket = _classify_ai_rejection(ai_summary)
                        rejections[bucket] = rejections.get(bucket, 0) + 1
                        continue

                    prop_data["matched_user_email"] = email
                    prop_data["ai_score"] = ai_score
                    prop_data["ai_summary"] = ai_summary
                    prop_data["monthly_repayment"] = analysis.get("monthly_repayment_estimate")
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
                            f"ציון {ai_score}",
                            "success",
                        )
                    except Exception:
                        pass

                # Push incremental progress to the UI after every batch
                log(f"  ✅ אצווה הושלמה — {total_matches} התאמות עד כה")

        log(f"📊 בסריקה זו: נסרקו {total_found} דירות, נשמרו {total_matches} התאמות חדשות")
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
            state["rejections"] = dict(rejections)
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
    """Return {"status":"started"} immediately; scan runs in a background task."""
    # ── Guard: don't double-start ──
    with _scan_lock:
        if _scan_states.get(email, {}).get("running"):
            return {"status": "already_running"}
        # Mark as started *before* queuing so /scan/status shows activity instantly
        _scan_states[email] = {
            "running": True,
            "finished": False,
            "message": "מתחיל סריקה...",
            "total_found": 0,
            "total_matches": 0,
            "log": [],
        }

    # ── Queue background work and return immediately ──
    background_tasks.add_task(_run_scan_bg, email, db)
    print(f"DEBUG: /scan POST returning 'started' for {email}", flush=True)
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
                "rejections": {},
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
