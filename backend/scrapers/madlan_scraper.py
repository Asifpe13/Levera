"""
Madlan scraper — uses curl_cffi to bypass bot protection.
Parses property cards from HTML using BeautifulSoup.
Extracts real listing ID from URL path (e.g. /listing/12345) for correct links.
"""
import re
import time
from typing import Optional
from urllib.parse import quote, urlparse

from loguru import logger

from scrapers.base_scraper import BaseScraper

DEAL_PATHS = {"sale": "forsale", "rent": "rent"}

# ערכי path שלא נחשבים כמזהה מודעה אמיתי (class names, routes וכו')
INVALID_LISTING_SEGMENTS = frozenset({
    "listed-bulletin-clickable", "listing", "listings", "list", "clickable",
    "bulletin", "card", "item", "",
})


class MadlanScraper(BaseScraper):
    SOURCE_NAME = "madlan"
    BASE_URL = "https://www.madlan.co.il"

    def __init__(self, deal_type: str = "sale", delay: float = 2.5):
        super().__init__(deal_type=deal_type)
        self.delay = delay
        self.deal_path = DEAL_PATHS.get(deal_type, "forsale")
        self._session = None

    @property
    def session(self):
        if self._session is None:
            from curl_cffi import requests as curl_requests
            self._session = curl_requests.Session(impersonate="chrome")
        return self._session

    def search(self, city: str, rooms_min: int = 1, rooms_max: int = 8,
               price_max: Optional[float] = None, page: int = 1) -> list[dict]:
        city_slug = quote(city.replace(" ", "-").replace(" - ", "-"))
        url = f"{self.BASE_URL}/listings/{self.deal_path}/{city_slug}"
        params: dict = {}
        if rooms_min > 1 or rooms_max < 8:
            params["rooms"] = f"{rooms_min}-{rooms_max}"
        if price_max:
            params["maxPrice"] = int(price_max)
        if page > 1:
            params["page"] = page

        try:
            time.sleep(self.delay)
            resp = self.session.get(url, params=params)
            if resp.status_code != 200:
                logger.warning(f"[madlan] HTTP {resp.status_code} for {city}")
                return []
        except Exception as e:
            logger.error(f"[madlan] Request failed for {city}: {e}")
            return []

        return self._parse_cards(resp.text, city)

    def _parse_cards(self, html: str, city: str) -> list[dict]:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        cards = soup.select("div.universal-card-body-wrapper")
        if not cards:
            cards = soup.select("div[class*='universal-card']")

        if not cards:
            logger.debug(f"[madlan] No property cards found for {city}")
            return []

        properties = []
        for card in cards[:30]:
            try:
                prop = self._extract_card(card, city)
                if prop and prop.get("price"):
                    properties.append(prop)
            except Exception:
                continue

        if properties:
            logger.info(f"[madlan] Found {len(properties)} listings for {city}")
        return properties

    def _extract_card(self, card, city: str) -> Optional[dict]:
        text = card.get_text(separator=" | ", strip=True)
        if not text:
            return None

        price = self._extract_price(text)
        if not price or price < 1000:
            return None

        rooms = self._extract_rooms(text)
        floor = self._extract_floor(text)
        sqm = self._extract_sqm(text)
        prop_type = self._extract_prop_type(text)

        parent = card.parent
        link = ""
        card_id = ""
        for _ in range(5):
            if parent is None:
                break
            for a_tag in parent.find_all("a", href=True):
                href = a_tag.get("href", "").strip()
                if not href or "/listing/" not in href:
                    continue
                full_url = href if href.startswith("http") else f"{self.BASE_URL}{href}"
                parsed = urlparse(full_url)
                path = (parsed.path or "").strip("/")
                parts = [p for p in path.split("/") if p]
                if not parts:
                    continue
                idx = next((i for i, seg in enumerate(parts) if seg == "listing"), -1)
                if idx >= 0 and idx + 1 < len(parts):
                    candidate_id = parts[idx + 1]
                    if candidate_id not in INVALID_LISTING_SEGMENTS and not any(
                        bad in candidate_id.lower() for bad in ("clickable", "bulletin", "listed")
                    ):
                        card_id = candidate_id
                        link = full_url
                        break
                elif len(parts) >= 1 and parts[-1] not in INVALID_LISTING_SEGMENTS:
                    candidate_id = parts[-1]
                    if not any(bad in candidate_id.lower() for bad in ("clickable", "bulletin", "listed")):
                        card_id = candidate_id
                        link = full_url
                        break
            if link and card_id:
                break
            parent = parent.parent

        if not link and card.parent:
            a_tag = card.parent.find("a", href=True)
            if a_tag:
                href = a_tag.get("href", "").strip()
                if href and "/listing/" in href:
                    full_url = href if href.startswith("http") else f"{self.BASE_URL}{href}"
                    parsed = urlparse(full_url)
                    path = (parsed.path or "").strip("/")
                    segs = [s for s in path.split("/") if s]
                    if segs and segs[-1] not in INVALID_LISTING_SEGMENTS and "clickable" not in segs[-1].lower():
                        card_id = card_id or segs[-1]
                        link = full_url

        img = ""
        img_parent = card.parent
        for _ in range(5):
            if img_parent is None:
                break
            img_tag = img_parent.find("img", src=True)
            if img_tag:
                img = img_tag.get("src", "")
                break
            img_parent = img_parent.parent

        if not card_id and card.parent:
            p = card.parent
            for _ in range(5):
                if p is None:
                    break
                if p.get("data-auto"):
                    auto = p.get("data-auto", "").strip()
                    if auto and auto not in INVALID_LISTING_SEGMENTS and "clickable" not in auto.lower():
                        card_id = auto
                        break
                p = p.parent

        return {
            "source": self.SOURCE_NAME,
            "source_id": card_id or None,
            "deal_type": self.deal_type,
            "title": f"{prop_type} ב{city}" if prop_type else f"נכס ב{city}",
            "city": city,
            "neighborhood": "",
            "address": "",
            "rooms": rooms,
            "floor": floor,
            "size_sqm": sqm,
            "price": price,
            "description": text[:200],
            "image_url": img,
            "listing_url": link,
            "property_type": prop_type,
            "is_new": "חדש" in text,
            "has_parking": "חניה" in text,
            "has_elevator": "מעלית" in text,
            "has_balcony": "מרפסת" in text,
            "has_storage": "מחסן" in text,
            "has_mamad": 'ממ"ד' in text or "ממד" in text,
            "raw_data": {"card_text": text[:500]},
        }

    @staticmethod
    def _extract_price(text: str) -> Optional[float]:
        m = re.search(r'([\d,]+)\s*₪?', text)
        if m:
            digits = m.group(1).replace(",", "")
            try:
                val = float(digits)
                return val if val > 10000 else None
            except ValueError:
                return None
        return None

    @staticmethod
    def _extract_rooms(text: str) -> Optional[float]:
        m = re.search(r'([\d.]+)\s*חד', text)
        return float(m.group(1)) if m else None

    @staticmethod
    def _extract_floor(text: str) -> Optional[int]:
        m = re.search(r'קומה\s*(\d+)', text)
        return int(m.group(1)) if m else None

    @staticmethod
    def _extract_sqm(text: str) -> Optional[float]:
        m = re.search(r'([\d,]+)\s*מ"ר', text)
        if m:
            try:
                return float(m.group(1).replace(",", ""))
            except ValueError:
                return None
        return None

    @staticmethod
    def _extract_prop_type(text: str) -> str:
        for t in ("דירה", "דירת גן", "פנטהאוז", "קוטג'", "דופלקס", "בית פרטי", "מגרש", "סטודיו"):
            if t in text:
                return t
        return ""

    def __del__(self):
        try:
            if self._session:
                self._session.close()
        except Exception:
            pass
