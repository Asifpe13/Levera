import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

MARKET_SETTINGS = {
    "interest_rate": 0.045,
    "loan_term_years": 30,
}

# חוק המשכנתא בישראל — בית ראשון: נדרש 25% הון עצמי ממחיר הדירה (משרד האוצר / פיקוח בנק ישראל)
FIRST_HOME_MIN_EQUITY_PCT = 0.25  # 25%

# דרישות הון עצמי לפי מספר דירה:
# 1 = דירה ראשונה, 2/3 = דירות נוספות (השקעה) — לרוב 50% הון עצמי.
HOME_EQUITY_BY_HOME_INDEX: dict[int, float] = {
    1: FIRST_HOME_MIN_EQUITY_PCT,
    2: 0.50,
    3: 0.50,
}


# ערכי source_id שלא נחשבים כמזהה מודעה תקף (מניעת קישורים שבורים)
INVALID_SOURCE_IDS = frozenset({
    "listed-bulletin-clickable", "listing", "listings", "list", "clickable",
    "bulletin", "card", "item", "none", "null",
})


def build_listing_url(source: str, source_id: Optional[str], deal_type: Optional[str] = None) -> str:
    """בונה קישור למודעה כש־listing_url חסר. מחזיר מחרוזת ריקה אם אין source_id תקף."""
    raw = (source_id and str(source_id).strip()) or ""
    if not raw or raw.lower() in INVALID_SOURCE_IDS:
        return ""
    if any(bad in raw.lower() for bad in ("clickable", "bulletin", "listed-bulletin")):
        return ""
    source = (source or "").lower().strip()
    deal = (deal_type or "sale").lower()
    if source == "yad2":
        return f"https://www.yad2.co.il/item/{raw}"
    if source == "madlan":
        return f"https://www.madlan.co.il/listing/{raw}"
    if source == "homeless":
        seg = "rent" if deal == "rent" else "sale"
        return f"https://www.homeless.co.il/{seg}/viewad,{raw}.aspx"
    if source == "winwin":
        path = "ForRent" if deal == "rent" else "ForSale"
        return f"https://www.winwin.co.il/RealEstate/{path}/Apartments.aspx?id={raw}"
    return ""


ALL_CITIES = [
    "אבו גוש",
    "אבן יהודה",
    "אום אל-פחם",
    "אופקים",
    "אור יהודה",
    "אור עקיבא",
    "אזור",
    "אילת",
    "אלעד",
    "אלפי מנשה",
    "אפרת",
    "אריאל",
    "אשדוד",
    "אשקלון",
    "באקה אל-גרביה",
    "באר יעקב",
    "באר שבע",
    "בית אריה",
    "בית דגן",
    "בית שאן",
    "בית שמש",
    "ביתר עילית",
    "בני ברק",
    "בנימינה-גבעת עדה",
    "בת ים",
    "ג'לג'וליה",
    "ג'סר אל-זרקא",
    "ג'ת",
    "גבעת זאב",
    "גבעת שמואל",
    "גבעתיים",
    "גדרה",
    "גן יבנה",
    "גני תקווה",
    "דימונה",
    "דליית אל-כרמל",
    "הוד השרון",
    "הרצליה",
    "זכרון יעקב",
    "חדרה",
    "חולון",
    "חיפה",
    "חצור הגלילית",
    "חריש",
    "טבריה",
    "טייבה",
    "טירה",
    "טירת כרמל",
    "טמרה",
    "יבנה",
    "יהוד-מונוסון",
    "יוקנעם עילית",
    "ירוחם",
    "ירושלים",
    "כוכב יאיר-צור יגאל",
    "כפר יונה",
    "כפר סבא",
    "כפר קאסם",
    "כפר קרע",
    "כרמיאל",
    "לוד",
    "להבים",
    "לקייה",
    "מבשרת ציון",
    "מגאר",
    "מגדל העמק",
    "מג'ד אל-כרום",
    "מודיעין עילית",
    "מודיעין-מכבים-רעות",
    "מזכרת בתיה",
    "מיתר",
    "מעלה אדומים",
    "מעלות-תרשיחא",
    "מצפה רמון",
    "נהריה",
    "נוף הגליל",
    "נס ציונה",
    "נשר",
    "נצרת",
    "נתיבות",
    "נתניה",
    "סחנין",
    "עומר",
    "עכו",
    "עפולה",
    "עראבה",
    "ערד",
    "עתלית",
    "פרדס חנה-כרכור",
    "פרדסיה",
    "פתח תקווה",
    "צפת",
    "קדימה-צורן",
    "קיסריה",
    "קלנסווה",
    "קצרין",
    "קרית אונו",
    "קרית אתא",
    "קרית ביאליק",
    "קרית גת",
    "קרית ים",
    "קרית מוצקין",
    "קרית מלאכי",
    "קרית שמונה",
    "קרני שומרון",
    "ראש העין",
    "ראשון לציון",
    "רהט",
    "רחובות",
    "רכסים",
    "רמלה",
    "רמת גן",
    "רמת השרון",
    "רעננה",
    "שגב-שלום",
    "שדרות",
    "שוהם",
    "שלומי",
    "שפרעם",
    "תל אביב - יפו",
    "תל מונד",
]

MIN_AI_SCORE_FOR_ALERT = int(os.getenv("MIN_AI_SCORE_FOR_ALERT", "40"))
SCAN_INTERVAL_MINUTES = int(os.getenv("SCAN_INTERVAL_MINUTES", "60"))
# Delay (seconds) between Gemini API calls during scan to avoid 429 rate limit (free tier)
GEMINI_DELAY_SECONDS = float(os.getenv("GEMINI_DELAY_SECONDS", "2.0"))
