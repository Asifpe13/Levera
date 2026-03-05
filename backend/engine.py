"""
Core orchestration engine: ties scrapers, AI, DB, and email together.
Handles multiple scrapers, buy/rent/both, per-user scanning, price history, and SaaS features.
"""
import time
from datetime import datetime, timezone
from loguru import logger

from config import MIN_AI_SCORE_FOR_ALERT, build_listing_url, GEMINI_DELAY_SECONDS
from logic import (
    check_property_fit,
    estimate_monthly_rent,
    calculate_annual_yield,
    get_market_value_label,
)
from database.db import DatabaseManager
from scrapers.yad2_api_scraper import Yad2ApiScraper
from scrapers.madlan_scraper import MadlanScraper
from scrapers.homeless_scraper import HomelessScraper
from scrapers.winwin_scraper import WinWinScraper
from services.ai_service import AIService
from services.email_service import EmailService
from services.market_validator import enrich_property_with_market


def _build_scrapers(deal_type: str) -> list:
    return [
        Yad2ApiScraper(deal_type=deal_type),
        MadlanScraper(deal_type=deal_type),
        HomelessScraper(deal_type=deal_type),
        WinWinScraper(deal_type=deal_type),
    ]


def _enrich_property_insights(prop_data: dict, city_avg: dict, ai: AIService) -> None:
    """Set estimated_rent, annual_yield_pct, value_label, neighborhood_insights. In-place."""
    price = prop_data.get("price") or 0
    rooms = prop_data.get("rooms")
    city = (prop_data.get("city") or "").strip()
    if price > 0 and prop_data.get("deal_type") == "sale":
        rent = estimate_monthly_rent(prop_data)
        if rent:
            prop_data["estimated_rent"] = rent
            prop_data["annual_yield_pct"] = calculate_annual_yield(price, rent)
    avg_ppr = city_avg.get(city) if city else None
    prop_data["value_label"] = get_market_value_label(price, rooms or 0, avg_ppr)
    insights = ai.get_neighborhood_insights(city, prop_data.get("address"))
    prop_data["neighborhood_insights"] = insights.get("summary") or ""

    # Market price comparison (gov sales data) for any Israeli address
    if prop_data.get("deal_type") == "sale" and city and ai.client:
        try:
            enrich_property_with_market(prop_data, ai.client, model_name=getattr(ai, "model_name", "gemini-2.0-flash"))
        except Exception as e:
            logger.debug(f"Market validation skipped for {city}: {e}")


class ScanEngine:
    def __init__(self, db: DatabaseManager = None, ai: AIService = None,
                 email: EmailService = None):
        self.db = db or DatabaseManager()
        self.ai = ai or AIService()
        self.email = email or EmailService()

    def run_scan_for_all_users(self):
        users = self.db.get_active_users()
        if not users:
            logger.warning("No active users found")
            return

        for user in users:
            try:
                self.run_scan_for_user(user)
            except Exception as e:
                logger.error(f"Scan failed for user {user['email']}: {e}")

    def run_scan_for_user(self, user: dict):
        user_email = user["email"]
        user_name = user.get("name", user_email)
        logger.info(f"Scanning for user: {user_name} ({user_email})")

        search_type = (user.get("search_type") or "both").lower().strip()
        # מכירה בלבד = רק דירות למכירה (מתעלמים מתקציב שכירות). השכרה בלבד = רק דירות להשכרה (מתעלמים מהון עצמי).
        deal_types = []
        if search_type in ("buy", "both", "sale"):
            deal_types.append("sale")
        if search_type in ("rent", "both"):
            deal_types.append("rent")

        user_prefs = {
            "target_cities": user.get("target_cities", []),
            "search_type": search_type,
            "equity": user.get("equity", 0),
            "monthly_income": user.get("monthly_income", 0),
            "room_range_min": user.get("room_range_min", 1),
            "room_range_max": user.get("room_range_max", 8),
            "max_price": user.get("max_price") if "sale" in deal_types else None,
            "max_repayment_ratio": user.get("max_repayment_ratio", 0.4),
            "rent_room_range_min": user.get("rent_room_range_min", 1),
            "rent_room_range_max": user.get("rent_room_range_max", 8),
            "max_rent": user.get("max_rent") if "rent" in deal_types else None,
            "extra_preferences": user.get("extra_preferences"),
        }

        all_raw_properties = []
        for dt in deal_types:
            scrapers = _build_scrapers(dt)
            rooms_min = user_prefs["rent_room_range_min"] if dt == "rent" else user_prefs["room_range_min"]
            rooms_max = user_prefs["rent_room_range_max"] if dt == "rent" else user_prefs["room_range_max"]
            price_max = user_prefs["max_rent"] if dt == "rent" else user_prefs["max_price"]
            for scraper in scrapers:
                try:
                    results = scraper.search_all_cities(
                        cities=user_prefs["target_cities"],
                        rooms_min=rooms_min,
                        rooms_max=rooms_max,
                        price_max=price_max,
                        max_pages=2,
                    )
                    all_raw_properties.extend(results)
                except Exception as e:
                    logger.error(f"Scraper {scraper.SOURCE_NAME}/{dt} failed: {e}")

        raw_count = len(all_raw_properties)
        logger.info(f"Found {raw_count} raw properties for {user_name}")

        new_matches = []
        city_avg = self.db.get_avg_price_per_room_by_city(user_email)

        for prop_data in all_raw_properties:
            source_id = prop_data.get("source_id")
            source = prop_data.get("source", "unknown")
            new_price = prop_data.get("price") or 0

            if source_id and self.db.property_exists(source, source_id):
                existing = self.db.get_property_by_source_id(source, source_id)
                if existing and new_price < (existing.get("price") or 0):
                    self.db.update_property_on_price_drop(
                        source, source_id, new_price,
                        matched_user_email=user_email,
                    )
                    fits, fit_detail = check_property_fit(prop_data, user_prefs)
                    if not fits:
                        continue
                    analysis = self.ai.analyze_property(prop_data, user_prefs)
                    prop_data["matched_user_email"] = user_email
                    prop_data["ai_score"] = analysis.get("score", 0)
                    prop_data["ai_summary"] = analysis.get("summary", "")
                    prop_data["monthly_repayment"] = analysis.get("monthly_repayment_estimate") or (
                        fit_detail if isinstance(fit_detail, (int, float)) else None
                    )
                    if prop_data.get("deal_type") == "sale" and prop_data.get("price"):
                        prop_data["loan_amount"] = max(0, prop_data["price"] - user_prefs.get("equity", 0))
                    prop_data["price_drop"] = True
                    _enrich_property_insights(prop_data, city_avg, self.ai)
                    if not (prop_data.get("listing_url") or "").strip():
                        prop_data["listing_url"] = build_listing_url(
                            prop_data.get("source"), prop_data.get("source_id"), prop_data.get("deal_type")
                        )
                    new_matches.append(prop_data)
                    if GEMINI_DELAY_SECONDS > 0:
                        time.sleep(GEMINI_DELAY_SECONDS)
                continue

            fits, fit_detail = check_property_fit(prop_data, user_prefs)
            if not fits:
                continue

            analysis = self.ai.analyze_property(prop_data, user_prefs)
            prop_data["matched_user_email"] = user_email
            prop_data["ai_score"] = analysis.get("score", 0)
            prop_data["ai_summary"] = analysis.get("summary", "")
            prop_data["monthly_repayment"] = analysis.get("monthly_repayment_estimate") or (
                fit_detail if isinstance(fit_detail, (int, float)) else None
            )
            if prop_data.get("deal_type") == "sale" and prop_data.get("price"):
                prop_data["loan_amount"] = max(0, prop_data["price"] - user_prefs.get("equity", 0))
            _enrich_property_insights(prop_data, city_avg, self.ai)
            if not (prop_data.get("listing_url") or "").strip():
                prop_data["listing_url"] = build_listing_url(
                    prop_data.get("source"), prop_data.get("source_id"), prop_data.get("deal_type")
                )

            if GEMINI_DELAY_SECONDS > 0:
                time.sleep(GEMINI_DELAY_SECONDS)

            try:
                saved = self.db.add_property(prop_data)
            except Exception as e:
                logger.error(f"Failed to save property: {e}")
                continue

            if analysis.get("score", 0) >= MIN_AI_SCORE_FOR_ALERT:
                new_matches.append(prop_data)

        self.db.log_search(
            user_email=user_email,
            search_params={
                "cities": user_prefs["target_cities"],
                "rooms": f"{user_prefs['room_range_min']}-{user_prefs['room_range_max']}",
                "deal_types": deal_types,
            },
            results_count=len(all_raw_properties),
            matches_count=len(new_matches),
        )

        if new_matches:
            for p in new_matches:
                if not (p.get("listing_url") or "").strip() and p.get("source") and p.get("source_id"):
                    p["listing_url"] = build_listing_url(
                        p.get("source"), p.get("source_id"), p.get("deal_type")
                    )
            logger.info(f"Sending alert for {len(new_matches)} new matches to {user_email}")
            self.email.send_property_alert(user_email, new_matches)

        matches_count = len(new_matches)
        logger.info(f"Scan complete for {user_name}: {matches_count} new matches")
        return {
            "raw_count": raw_count,
            "matches_count": matches_count,
        }

    def send_weekly_reports(self):
        users = self.db.get_active_users()
        for user in users:
            try:
                self._send_weekly_report_for_user(user)
            except Exception as e:
                logger.error(f"Weekly report failed for {user['email']}: {e}")

    def _send_weekly_report_for_user(self, user: dict):
        user_email = user["email"]
        user_name = user.get("name", user_email)

        properties = self.db.get_weekly_properties(user_email, days=7)

        if not properties:
            logger.info(f"No properties this week for {user_name}")
            return

        prop_dicts = []
        for p in properties:
            listing_url = (p.get("listing_url") or "").strip()
            if not listing_url and p.get("source") and p.get("source_id"):
                listing_url = build_listing_url(
                    p.get("source"), p.get("source_id"), p.get("deal_type")
                )
            prop_dicts.append({
                "city": p.get("city", ""),
                "neighborhood": p.get("neighborhood", ""),
                "address": p.get("address", ""),
                "rooms": p.get("rooms"),
                "floor": p.get("floor"),
                "size_sqm": p.get("size_sqm"),
                "price": p.get("price", 0),
                "deal_type": p.get("deal_type", "sale"),
                "source": p.get("source", ""),
                "ai_score": p.get("ai_score"),
                "ai_summary": p.get("ai_summary", ""),
                "listing_url": listing_url,
                "has_parking": p.get("has_parking"),
                "has_elevator": p.get("has_elevator"),
                "has_mamad": p.get("has_mamad"),
                "price_drop": p.get("price_drop", False),
                "estimated_rent": p.get("estimated_rent"),
                "annual_yield_pct": p.get("annual_yield_pct"),
                "value_label": p.get("value_label"),
                "neighborhood_insights": p.get("neighborhood_insights"),
                "market_confidence": p.get("market_confidence"),
                "market_avg_per_sqm": p.get("market_avg_per_sqm"),
                "market_summary_text": p.get("market_summary_text"),
                "loan_amount": p.get("loan_amount"),
            })

        ai_summary = self.ai.generate_weekly_summary(prop_dicts, user_name)

        self.email.send_weekly_report(
            to_email=user_email,
            user_name=user_name,
            properties=prop_dicts,
            ai_summary=ai_summary,
        )

        prop_ids = [p.get("_id") for p in properties if p.get("_id")]
        self.db.mark_report_sent(prop_ids)
        self.db.save_weekly_report(user_email, prop_ids, ai_summary)

        logger.info(f"Weekly report sent to {user_name} with {len(properties)} properties")
