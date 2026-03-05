import os
import re
import json
import time
from typing import Optional, Any

from loguru import logger

# Max retries on 429 (rate limit); wait between retries from API or default 60s
GEMINI_RATE_LIMIT_RETRIES = 2
GEMINI_RATE_LIMIT_DEFAULT_WAIT = 60


def _extract_retry_delay_seconds(error: Exception) -> float:
    """Parse 'Please retry in X.XXs' or retryDelay from Gemini 429 response."""
    msg = str(error)
    match = re.search(r"retry\s+in\s+([\d.]+)\s*s", msg, re.I)
    if match:
        return float(match.group(1))
    match = re.search(r"retryDelay[^\d]*([\d.]+)", msg, re.I)
    if match:
        return float(match.group(1))
    return float(GEMINI_RATE_LIMIT_DEFAULT_WAIT)


def _is_rate_limit_error(error: Exception) -> bool:
    return "429" in str(error) or "RESOURCE_EXHAUSTED" in str(error) or "quota" in str(error).lower()


def _generate_with_retry(client, model: str, contents: str, config: Any) -> Any:
    """Call generate_content with retry on 429 rate limit."""
    last_error = None
    for attempt in range(GEMINI_RATE_LIMIT_RETRIES + 1):
        try:
            return client.models.generate_content(model=model, contents=contents, config=config)
        except Exception as e:
            last_error = e
            if _is_rate_limit_error(e) and attempt < GEMINI_RATE_LIMIT_RETRIES:
                wait = _extract_retry_delay_seconds(e)
                logger.warning(f"Gemini rate limit (429), waiting {wait:.0f}s before retry ({attempt + 1}/{GEMINI_RATE_LIMIT_RETRIES + 1})")
                time.sleep(wait)
            else:
                raise
    raise last_error


class AIService:
    def __init__(self, api_key: Optional[str] = None, enabled: bool = True):
        """
        Wrapper around Gemini client.
        Set enabled=False to force deterministic fallback (no Gemini calls) – useful for load testing.
        """
        if not enabled:
            self.api_key = None
            self.client = None
            self.model_name = "gemini-2.0-flash"
            logger.info("Gemini AI service disabled (enabled=False) — using rule-based fallback only")
            return

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set — AI analysis will use rule-based fallback")
            self.client = None
            self.model_name = "gemini-2.0-flash"
        else:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                self.model_name = "gemini-2.0-flash"
                logger.info("Gemini AI service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                self.client = None

    def analyze_property(self, property_data: dict, user_prefs: dict) -> dict:
        """
        Uses Gemini to analyze how well a property matches user preferences.
        Returns {"score": 0-100, "summary": str, "pros": list, "cons": list}
        """
        if not self.client:
            return self._fallback_analysis(property_data, user_prefs)

        prompt = self._build_analysis_prompt(property_data, user_prefs)
        system_instruction = (
            'אתה מומחה נדל"ן ישראלי. תפקידך לנתח נכסים ולהעריך את ההתאמה שלהם לדרישות הרוכש. '
            "ענה תמיד ב-JSON תקין בלבד, ללא טקסט נוסף."
        )

        try:
            from google.genai import types

            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                max_output_tokens=1024,
                temperature=0.3,
            )
            response = _generate_with_retry(self.client, self.model_name, prompt, config)

            result_text = response.text.strip()
            if result_text.startswith("```"):
                result_text = result_text.split("\n", 1)[1]
                result_text = result_text.rsplit("```", 1)[0]

            return json.loads(result_text)

        except json.JSONDecodeError as e:
            logger.error(f"AI returned invalid JSON: {e}")
            return self._fallback_analysis(property_data, user_prefs)
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return self._fallback_analysis(property_data, user_prefs)

    def _build_analysis_prompt(self, property_data: dict, user_prefs: dict) -> str:
        price = property_data.get("price", 0)
        price_str = f"{price:,.0f}" if isinstance(price, (int, float)) else str(price)

        equity = user_prefs.get("equity", 0)
        equity_str = f"{equity:,.0f}" if isinstance(equity, (int, float)) else str(equity)

        income = user_prefs.get("monthly_income", 0)
        income_str = f"{income:,.0f}" if isinstance(income, (int, float)) else str(income)

        ratio = user_prefs.get("max_repayment_ratio", 0.4)
        ratio_pct = ratio * 100 if isinstance(ratio, (int, float)) else ratio

        return f"""נתח את הנכס הבא עבור הרוכש וציין ציון התאמה מ-0 עד 100.
חשוב: בישראל בנקים לא מאשרים משכנתא שהחזר חודשי עולה על {ratio_pct}% מההכנסה. בית ראשון לפי חוק המשכנתא דורש 25% הון עצמי ממחיר הדירה.

== פרטי הנכס ==
עיר: {property_data.get('city', 'לא ידוע')}
שכונה: {property_data.get('neighborhood', 'לא ידוע')}
כתובת: {property_data.get('address', 'לא ידוע')}
חדרים: {property_data.get('rooms', 'לא ידוע')}
קומה: {property_data.get('floor', 'לא ידוע')}
שטח: {property_data.get('size_sqm', 'לא ידוע')} מ"ר
מחיר: {price_str} ₪
חניה: {'כן' if property_data.get('has_parking') else 'לא'}
מעלית: {'כן' if property_data.get('has_elevator') else 'לא'}
מרפסת: {'כן' if property_data.get('has_balcony') else 'לא'}
ממ"ד: {'כן' if property_data.get('has_mamad') else 'לא'}
מחסן: {'כן' if property_data.get('has_storage') else 'לא'}
סוג: {property_data.get('property_type', 'לא ידוע')}
תיאור: {str(property_data.get('description', 'אין תיאור'))[:500]}

== דרישות הרוכש ==
הון עצמי: {equity_str} ₪
הכנסה חודשית: {income_str} ₪
ערים מועדפות: {', '.join(user_prefs.get('target_cities', []))}
טווח חדרים: {user_prefs.get('room_range_min', 1)}-{user_prefs.get('room_range_max', 8)}
יחס החזר מקסימלי: {ratio_pct}%
דרישות נוספות: {user_prefs.get('extra_preferences', 'אין')}

החזר JSON בפורמט הבא בלבד:
{{
  "score": <0-100>,
  "summary": "<סיכום קצר בעברית - 2-3 משפטים>",
  "pros": ["<יתרון 1>", "<יתרון 2>"],
  "cons": ["<חיסרון 1>", "<חיסרון 2>"],
  "monthly_repayment_estimate": <number>,
  "recommendation": "<קנה / שקול / עבור>"
}}"""

    def _fallback_analysis(self, property_data: dict, user_prefs: dict) -> dict:
        """Rule-based fallback when AI is unavailable."""
        score = 50
        pros = []
        cons = []

        city = property_data.get("city", "")
        target_cities = user_prefs.get("target_cities", [])
        if city in target_cities:
            score += 15
            pros.append(f"נמצא באזור מבוקש: {city}")
        else:
            score -= 20
            cons.append(f"{city} לא ברשימת הערים המועדפות")

        rooms = property_data.get("rooms")
        room_min = user_prefs.get("room_range_min", 1)
        room_max = user_prefs.get("room_range_max", 8)
        if rooms and room_min <= rooms <= room_max:
            score += 10
            pros.append(f"{rooms} חדרים - בטווח המבוקש")
        elif rooms:
            score -= 10
            cons.append(f"{rooms} חדרים - מחוץ לטווח ({room_min}-{room_max})")

        price = property_data.get("price", 0)
        equity = user_prefs.get("equity", 0)
        income = user_prefs.get("monthly_income", 0)
        ratio = user_prefs.get("max_repayment_ratio", 0.4)

        if price and equity and income:
            from logic import calculate_monthly_repayment
            repayment = calculate_monthly_repayment(price, equity, 0.045, 30)
            max_repayment = income * ratio

            if repayment <= max_repayment:
                score += 15
                pros.append(f"החזר חודשי {repayment:,.0f}₪ - בתוך היכולת")
            else:
                score -= 15
                cons.append(f"החזר חודשי {repayment:,.0f}₪ - מעל היכולת ({max_repayment:,.0f}₪)")
        else:
            repayment = 0

        if property_data.get("has_parking"):
            score += 3
            pros.append("יש חניה")
        if property_data.get("has_mamad"):
            score += 3
            pros.append('יש ממ"ד')
        if property_data.get("has_elevator"):
            score += 2
            pros.append("יש מעלית")

        score = max(0, min(100, score))

        recommendation = "קנה" if score >= 70 else "שקול" if score >= 45 else "עבור"

        return {
            "score": score,
            "summary": f"ציון התאמה: {score}/100. "
                       + (f"החזר חודשי משוער: {repayment:,.0f}₪. " if repayment else "")
                       + f"המלצה: {recommendation}.",
            "pros": pros,
            "cons": cons,
            "monthly_repayment_estimate": round(repayment) if repayment else None,
            "recommendation": recommendation,
        }

    def generate_weekly_summary(self, properties: list[dict], user_name: str) -> str:
        """Generate a natural language weekly summary."""
        if not self.client:
            return self._fallback_weekly_summary(properties, user_name)

        props_text = "\n".join(
            f"- {p.get('city', '?')}, {p.get('rooms', '?')} חד', "
            f"{p.get('price', 0):,.0f}₪, ציון: {p.get('ai_score', '?')}"
            for p in properties
        )

        try:
            from google.genai import types
            contents = f"""כתוב סיכום שבועי קצר ומקצועי עבור {user_name}.
נמצאו {len(properties)} דירות השבוע:

{props_text}

כתוב סיכום של 3-5 משפטים בעברית, כולל:
1. כמה דירות נמצאו
2. טווח מחירים
3. הדירה הטובה ביותר
4. המלצה כללית"""
            config = types.GenerateContentConfig(
                system_instruction='אתה יועץ נדל"ן מקצועי שכותב דו"חות שבועיים ללקוחות.',
                max_output_tokens=1500,
                temperature=0.5,
            )
            response = _generate_with_retry(self.client, self.model_name, contents, config)
            return response.text
        except Exception as e:
            logger.error(f"AI weekly summary failed: {e}")
            return self._fallback_weekly_summary(properties, user_name)

    def get_neighborhood_insights(self, city: str, address: Optional[str] = None) -> dict:
        """
        AI neighborhood insights: proximity to schools, parks, future development.
        Returns { "summary": str, "pros": list[str], "cons": list[str] }. Generic.
        """
        if not self.client:
            return {"summary": "", "pros": [], "cons": []}
        location = f"{address or ''}, {city}".strip(", ")
        try:
            from google.genai import types
            contents = f"""נתח את האזור/שכונה עבור הכתובת הבאה בישראל:
{location}

תן תובנות קצרות: קרבה לבתי ספר, גנים, פארקים, פיתוח עתידי, תחבורה, ביטחון.
החזר JSON בלבד בפורמט:
{{ "summary": "<2-3 משפטים בעברית>", "pros": ["יתרון 1", "יתרון 2"], "cons": ["חיסרון 1"] }}"""
            config = types.GenerateContentConfig(
                system_instruction='אתה יועץ נדל"ן ישראלי. ענה ב-JSON תקין בלבד.',
                max_output_tokens=512,
                temperature=0.3,
            )
            response = _generate_with_retry(self.client, self.model_name, contents, config)
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0]
            import json
            return json.loads(text)
        except Exception as e:
            logger.warning(f"Neighborhood insights failed: {e}")
            return {"summary": "", "pros": [], "cons": []}

    def _fallback_weekly_summary(self, properties: list[dict], user_name: str) -> str:
        if not properties:
            return f"שלום {user_name}, השבוע לא נמצאו דירות חדשות התואמות את הדרישות שלך."

        prices = [p.get("price", 0) for p in properties if p.get("price")]
        min_price = min(prices) if prices else 0
        max_price = max(prices) if prices else 0
        best = max(properties, key=lambda p: p.get("ai_score", 0))

        return (
            f"שלום {user_name},\n\n"
            f"השבוע נמצאו {len(properties)} דירות התואמות את הדרישות שלך.\n"
            f"טווח מחירים: {min_price:,.0f}₪ - {max_price:,.0f}₪\n"
            f"הדירה המומלצת ביותר: {best.get('city', '?')}, "
            f"{best.get('rooms', '?')} חדרים, {best.get('price', 0):,.0f}₪ "
            f"(ציון: {best.get('ai_score', '?')}/100)\n\n"
            f"מומלץ לבדוק את הדירות המסומנות בציון גבוה."
        )
