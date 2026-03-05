"""
Market price comparison using Gemini with Google Search grounding.
Fetches government sales data (Rachus HaMisim / רכוש המסים) for any Israeli address
and compares listing price to area average.
"""
import json
import re
from typing import Optional

from loguru import logger


def _extract_address_parts(prop_data: dict) -> tuple[str, str, str]:
    """Return (street_or_area, city, rooms_str) for the prompt."""
    city = (prop_data.get("city") or "").strip() or "לא ידוע"
    address = (prop_data.get("address") or "").strip()
    neighborhood = (prop_data.get("neighborhood") or "").strip()
    street_or_area = address or neighborhood or city
    rooms = prop_data.get("rooms")
    if rooms is not None:
        try:
            rooms_str = str(int(rooms)) if isinstance(rooms, (int, float)) else str(rooms)
        except (ValueError, TypeError):
            rooms_str = "דומה"
    else:
        rooms_str = "דומה"
    return street_or_area, city, rooms_str


def _build_prompt(street_or_area: str, city: str, rooms_str: str, size_sqm: Optional[float]) -> str:
    size_note = f" (שטח דומה: {size_sqm} מ\"ר)" if size_sqm else ""
    return f"""Search for recent Israeli government real estate sales data (מרשם המקרקעין / רכוש המסים / משרד המשפטים או נתוני מכירות מדינה) for:
- Street/area: {street_or_area}
- City: {city}
- Apartment size: {rooms_str} rooms{size_note}

Find the average price per square meter (מחיר למטר רבוע) for similar apartments in this street or area in 2024-2026. If you find only total sale prices, derive average per SQM if possible.

Reply with a JSON object only, no other text:
{{
  "avg_price_per_sqm": <number in ILS, or null if not found>,
  "source_note": "<short Hebrew note about data source, e.g. רכוש המסים / Gov data>",
  "confidence": <0-100 how reliable the data is>
}}"""


def _parse_grounded_response(text: str) -> Optional[dict]:
    """Extract avg_price_per_sqm, source_note, confidence from model response."""
    if not text or not text.strip():
        return None
    text = text.strip()
    # Strip markdown code block if present
    if "```" in text:
        try:
            start = text.index("```") + 3
            if "json" in text[:start].lower():
                start = text.index("\n", start) + 1 if "\n" in text[start:] else start
            end = text.index("```", start)
            text = text[start:end]
        except ValueError:
            pass
    # Try to find JSON object (allow nested braces)
    start = text.find("{")
    if start >= 0:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start : i + 1])
                    except json.JSONDecodeError:
                        break
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Fallback: look for a number that could be price per sqm (e.g. 15000-50000 range)
    num_match = re.search(r"[\d,]+(?:\.[\d]+)?", text.replace(",", ""))
    if num_match:
        try:
            val = float(num_match.group().replace(",", ""))
            if 5_000 < val < 200_000:  # plausible ILS per sqm
                return {"avg_price_per_sqm": val, "source_note": "נתונים ממקור חיצוני", "confidence": 50}
        except ValueError:
            pass
    return None


def get_market_comparison(
    prop_data: dict,
    gemini_client: Optional[object],
    model_name: str = "gemini-2.0-flash",
    use_grounding: bool = True,
) -> Optional[dict]:
    """
    Compare listing price to government/area sales data using Gemini (with optional Google Search grounding).

    Args:
        prop_data: dict with city, address or neighborhood, rooms, size_sqm, price
        gemini_client: genai.Client()
        model_name: model that supports grounding (e.g. gemini-2.0-flash, gemini-1.5-pro)
        use_grounding: if True, use Google Search tool for live data

    Returns:
        dict with market_confidence, market_avg_per_sqm, price_deviation_pct, market_summary_text
        or None on failure or if not applicable (e.g. rent).
    """
    if not gemini_client:
        return None
    deal_type = (prop_data.get("deal_type") or "sale").lower()
    if deal_type != "sale":
        return None

    street_or_area, city, rooms_str = _extract_address_parts(prop_data)
    if not city or city == "לא ידוע":
        return None

    price = prop_data.get("price")
    size_sqm = prop_data.get("size_sqm")
    if not price or price <= 0:
        return None

    prompt = _build_prompt(street_or_area, city, rooms_str, size_sqm)

    try:
        from google.genai import types

        config_kw: dict = {
            "max_output_tokens": 1024,
            "temperature": 0.2,
            "system_instruction": 'You are a real estate data analyst for Israel. Reply only with valid JSON. Use Hebrew for source_note.',
        }
        if use_grounding:
            try:
                config_kw["tools"] = [types.Tool(google_search=types.GoogleSearch())]
            except Exception:
                config_kw["tools"] = []

        config = types.GenerateContentConfig(**config_kw)
        response = gemini_client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config,
        )
        result_text = (response.text or "").strip()
        parsed = _parse_grounded_response(result_text)
        if not parsed or parsed.get("avg_price_per_sqm") is None:
            return None

        avg_sqm = float(parsed["avg_price_per_sqm"])
        if avg_sqm <= 0:
            return None

        source_note = (parsed.get("source_note") or "נתוני מדינה").strip()
        data_confidence = min(100, max(0, int(parsed.get("confidence", 50))))

        # Listing price per sqm (use size_sqm if available, else estimate from rooms)
        if size_sqm and size_sqm > 0:
            listing_per_sqm = price / size_sqm
        else:
            # Rough: ~35 sqm per room
            est_sqm = (prop_data.get("rooms") or 3) * 35
            listing_per_sqm = price / est_sqm if est_sqm else None
        if listing_per_sqm is None or listing_per_sqm <= 0:
            return None

        deviation_pct = ((listing_per_sqm - avg_sqm) / avg_sqm) * 100
        # Market confidence: high when close to market, penalize large deviation; blend with data_confidence
        deviation_penalty = min(100, abs(deviation_pct) * 1.5)
        market_confidence = max(0, min(100, round(data_confidence - deviation_penalty + 50)))

        avg_formatted = f"{avg_sqm:,.0f}"
        summary_text = f"דירות דומות באזור נמכרו בממוצע ב־₪{avg_formatted} למ\"ר ({source_note})."

        return {
            "market_confidence": market_confidence,
            "market_avg_per_sqm": round(avg_sqm, 0),
            "price_deviation_pct": round(deviation_pct, 1),
            "market_summary_text": summary_text,
        }
    except Exception as e:
        logger.warning(f"Market validator failed for {city} {street_or_area}: {e}")
        return None


def enrich_property_with_market(prop_data: dict, gemini_client, model_name: str = "gemini-2.0-flash") -> None:
    """
    In-place: add market_confidence, market_avg_per_sqm, price_deviation_pct, market_summary_text to prop_data.
    No-op if client is None or comparison fails.
    """
    result = get_market_comparison(prop_data, gemini_client, model_name=model_name)
    if not result:
        return
    prop_data["market_confidence"] = result["market_confidence"]
    prop_data["market_avg_per_sqm"] = result["market_avg_per_sqm"]
    prop_data["price_deviation_pct"] = result["price_deviation_pct"]
    prop_data["market_summary_text"] = result["market_summary_text"]
