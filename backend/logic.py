import math
from typing import Optional, Callable

from config import MARKET_SETTINGS, FIRST_HOME_MIN_EQUITY_PCT, HOME_EQUITY_BY_HOME_INDEX

# Rough monthly rent (NIS) by city for yield estimation — generic mapping
DEFAULT_RENT_PER_SQM = 45
CITY_RENT_MULTIPLIER: dict[str, float] = {
    "תל אביב - יפו": 1.55,
    "הרצליה": 1.4,
    "רמת גן": 1.25,
    "גבעתיים": 1.3,
    "בני ברק": 1.1,
    "חיפה": 1.0,
    "ירושלים": 1.15,
    "באר שבע": 0.85,
    "אשדוד": 0.9,
    "נתניה": 1.05,
    "פתח תקווה": 1.1,
    "ראשון לציון": 1.05,
    "חולון": 1.0,
    "בת ים": 0.95,
}


def calculate_monthly_repayment(price: float, equity: float,
                                interest: float = None, years: int = None) -> float:
    if interest is None:
        interest = MARKET_SETTINGS["interest_rate"]
    if years is None:
        years = MARKET_SETTINGS["loan_term_years"]

    loan_amount = price - equity
    if loan_amount <= 0:
        return 0

    monthly_interest = interest / 12
    num_payments = years * 12

    repayment = loan_amount * (
        monthly_interest * (1 + monthly_interest) ** num_payments
    ) / (
        (1 + monthly_interest) ** num_payments - 1
    )
    return repayment


def get_mortgage_breakdown(
    price: float,
    equity: float,
    interest: float = None,
    years: int = None,
) -> dict:
    """
    פירוט משכנתא לפי חוק המשכנתא בישראל (בית ראשון: 25% הון עצמי).
    מחזיר: loan_amount (סכום המשכנתא), required_equity (הון נדרש לפי חוק), monthly_repayment, equity_ratio.
    """
    if interest is None:
        interest = MARKET_SETTINGS["interest_rate"]
    if years is None:
        years = MARKET_SETTINGS["loan_term_years"]
    required_equity = price * FIRST_HOME_MIN_EQUITY_PCT
    loan_amount = max(0, price - equity)
    monthly_repayment = calculate_monthly_repayment(price, equity, interest, years)
    return {
        "loan_amount": loan_amount,
        "required_equity_by_law": required_equity,
        "monthly_repayment": monthly_repayment,
        "equity_ratio": equity / price if price and price > 0 else 0,
        "first_home_min_equity_pct": FIRST_HOME_MIN_EQUITY_PCT,
    }


def check_property_fit(property_data: dict, user_data: dict) -> tuple[bool, str | float]:
    """
    בודק התאמת נכס להעדפות המשתמש.
    - במכירה: התייחסות להון עצמי + max_price (וגם החזר חודשי ביחס להכנסה).
    - בהשכרה: התייחסות רק ל-max_rent (לא להון עצמי ולא ל-max_price).
    """
    deal_type = (property_data.get("deal_type") or "sale").lower()
    is_rent = deal_type == "rent"
    user_search = (user_data.get("search_type") or "both").lower()

    # מכירה בלבד — רק נכסים למכירה; השכרה בלבד — רק נכסים להשכרה
    if user_search == "buy" or user_search == "sale":
        if is_rent:
            return False, "המשתמש חיפש מכירה בלבד — הנכס להשכרה"
    elif user_search == "rent":
        if not is_rent:
            return False, "המשתמש חיפש השכרה בלבד — הנכס למכירה"

    city = property_data.get("city", "")
    target_cities = user_data.get("target_cities", [])
    if city and target_cities and city not in target_cities:
        return False, "לא באזור המבוקש"

    rooms = property_data.get("rooms")
    if is_rent:
        room_min = user_data.get("rent_room_range_min", 1)
        room_max = user_data.get("rent_room_range_max", 8)
    else:
        room_min = user_data.get("room_range_min", 1)
        room_max = user_data.get("room_range_max", 8)
    if rooms is not None and not (room_min <= rooms <= room_max):
        return False, f"מספר חדרים ({rooms}) מחוץ לטווח ({room_min}-{room_max})"

    price = property_data.get("price", 0)
    if is_rent:
        # השכרה: בודקים רק max_rent (לא הון עצמי, לא max_price)
        max_rent = user_data.get("max_rent")
        if max_rent is not None and max_rent > 0 and price > max_rent:
            return False, f"שכר דירה {price:,.0f}₪ מעל התקציב ({max_rent:,.0f}₪)"
        return True, 0
    # מכירה: חוק המשכנתא — בית ראשון ~25% הון עצמי; דירות להשקעה לרוב דורשות הון עצמי גבוה יותר.
    max_price = user_data.get("max_price")
    if max_price and price > max_price:
        return False, f"מחיר {price:,.0f}₪ מעל התקציב ({max_price:,.0f}₪)"
    equity = user_data.get("equity", 0)
    income = user_data.get("monthly_income", 0)
    ratio = user_data.get("max_repayment_ratio", 0.4)

    # חוק המשכנתא בישראל:
    # - דירה ראשונה: ~75% מימון (25% הון עצמי)
    # - דירה שנייה/שלישית: בדרך־כלל 50% מימון (50% הון עצמי)
    home_index = int(user_data.get("home_index") or 1)
    equity_pct = HOME_EQUITY_BY_HOME_INDEX.get(
        home_index,
        0.50 if home_index > 1 else FIRST_HOME_MIN_EQUITY_PCT,
    )
    required_equity = price * equity_pct
    if equity < required_equity:
        return False, (
            f"לנכס מסוג זה נדרש לפחות {equity_pct * 100:.0f}% הון עצמי (חוק המשכנתא). "
            f"הון נדרש: {required_equity:,.0f}₪ (יש לך {equity:,.0f}₪)"
        )

    # ללא הכנסה חודשית אי־אפשר לוודא התאמה ליחס ההחזר — דוחים
    if not income or income <= 0:
        return False, "לא ניתן לבדוק התאמה למשכנתא ללא הכנסה חודשית (בנקים מגבילים החזר לאחוז מההכנסה)"

    repayment = calculate_monthly_repayment(price, equity)
    max_repayment = income * ratio
    if repayment > max_repayment:
        return False, (
            f"החזר חודשי {repayment:,.0f}₪ מעל {ratio * 100:.0f}% מההכנסה ({max_repayment:,.0f}₪) — בנקים לא יאשרו"
        )
    return True, round(repayment, 2)


def estimate_monthly_rent(property_data: dict, ai_estimate_func: Optional[Callable[[dict], Optional[float]]] = None) -> Optional[float]:
    """
    Estimate monthly rent for a property (for yield calculation).
    Uses city multiplier × size_sqm × default per-sqm rent, or AI if provided.
    Generic: works for any user.
    """
    if ai_estimate_func:
        try:
            rent = ai_estimate_func(property_data)
            if rent is not None and rent > 0:
                return rent
        except Exception:
            pass
    city = (property_data.get("city") or "").strip()
    size = property_data.get("size_sqm")
    rooms = property_data.get("rooms")
    mult = CITY_RENT_MULTIPLIER.get(city, 1.0)
    if size and size > 0:
        return round(DEFAULT_RENT_PER_SQM * size * mult, 0)
    if rooms and rooms > 0:
        return round(2500 * rooms * mult, 0)
    return None


def calculate_annual_yield(price: float, monthly_rent: float) -> float:
    """Annual yield % = (12 * monthly_rent) / price * 100. Generic."""
    if not price or price <= 0 or not monthly_rent or monthly_rent <= 0:
        return 0.0
    return round((12 * monthly_rent) / price * 100, 2)


def get_market_value_label(
    price: float,
    rooms: float,
    city_avg_price_per_room: Optional[float],
    threshold_low: float = 0.92,
    threshold_high: float = 1.08,
) -> str:
    """
    Compare price-per-room to city average. Generic.
    Returns: 'Below Market Value' | 'Fair Price' | 'Overpriced'
    """
    if not rooms or rooms <= 0 or city_avg_price_per_room is None or city_avg_price_per_room <= 0:
        return "Fair Price"
    price_per_room = price / rooms
    ratio = price_per_room / city_avg_price_per_room
    if ratio <= threshold_low:
        return "Below Market Value"
    if ratio >= threshold_high:
        return "Overpriced"
    return "Fair Price"
