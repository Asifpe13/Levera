"""
Homeless.co.il scraper — uses curl_cffi to bypass bot protection.
Parses property listings from search result pages.
"""
import re
import time
from typing import Optional

from loguru import logger

from scrapers.base_scraper import BaseScraper

DEAL_PATHS = {"sale": "sale", "rent": "rent"}


class HomelessScraper(BaseScraper):
    SOURCE_NAME = "homeless"
    BASE_URL = "https://www.homeless.co.il"

    def __init__(self, deal_type: str = "sale", delay: float = 3.0):
        super().__init__(deal_type=deal_type)
        self.delay = delay
        self.deal_path = DEAL_PATHS.get(deal_type, "sale")
        self._session = None

    @property
    def session(self):
        if self._session is None:
            from curl_cffi import requests as curl_requests
            self._session = curl_requests.Session(impersonate="chrome120")
        return self._session

    def search(self, city: str, rooms_min: int = 1, rooms_max: int = 8,
               price_max: Optional[float] = None, page: int = 1) -> list[dict]:
        url = f"{self.BASE_URL}/{self.deal_path}/apartments"
        params: dict = {"text": city}
        if page > 1:
            params["page"] = page

        for attempt in range(2):
            try:
                time.sleep(self.delay + attempt * 1.5)
                resp = self.session.get(url, params=params, timeout=25)
                if resp.status_code == 403:
                    logger.warning(f"[homeless] Blocked (403) for {city}, retrying with new session...")
                    self._session = None
                    time.sleep(3)
                    continue
                if resp.status_code != 200:
                    logger.warning(f"[homeless] HTTP {resp.status_code} for {city}")
                    return []
                return self._parse_listings(resp.text, city, rooms_min, rooms_max, price_max)
            except Exception as e:
                logger.warning(f"[homeless] Request failed for {city}: {e}")
                if attempt == 0:
                    self._session = None
                    time.sleep(2)
        return []

    def _parse_listings(self, html: str, city: str,
                        rooms_min: int, rooms_max: int,
                        price_max: Optional[float]) -> list[dict]:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        main = soup.find("div", id="main")
        if not main:
            main = soup

        links = main.find_all("a", href=re.compile(r"/(?:sale|rent)/viewad,\d+\.aspx"))

        properties = []
        seen_ids = set()

        for link in links[:40]:
            try:
                prop = self._extract_listing(link, city)
                if not prop:
                    continue
                if prop["source_id"] in seen_ids:
                    continue
                seen_ids.add(prop["source_id"])

                if prop.get("rooms") is not None:
                    if prop["rooms"] < rooms_min or prop["rooms"] > rooms_max:
                        continue
                if price_max and prop.get("price") and prop["price"] > price_max:
                    continue

                properties.append(prop)
            except Exception:
                continue

        if properties:
            logger.info(f"[homeless] Found {len(properties)} listings for {city}")
        return properties

    def _extract_listing(self, link_el, city: str) -> Optional[dict]:
        href = link_el.get("href", "")
        id_match = re.search(r"viewad,(\d+)\.aspx", href)
        if not id_match:
            return None
        listing_id = id_match.group(1)

        text = link_el.get_text(separator=" ", strip=True)
        if not text or len(text) < 10:
            return None

        price = self._extract_price(text)
        if not price or price < 1000:
            return None

        rooms = self._extract_rooms(text)
        sqm = self._extract_sqm(text)
        floor = self._extract_floor(text)

        neighborhood_match = re.search(r'שכונ[הת]\s+([^\d,]+)', text)
        neighborhood = neighborhood_match.group(1).strip() if neighborhood_match else ""

        address = ""
        address_match = re.search(r'רחוב\s+([^\d,]+)', text)
        if address_match:
            address = address_match.group(1).strip()

        listing_url = href if href.startswith("http") else f"{self.BASE_URL}{href}"

        img = ""
        img_el = link_el.find("img")
        if img_el:
            img = img_el.get("src", "") or img_el.get("data-src", "")

        return {
            "source": self.SOURCE_NAME,
            "source_id": listing_id,
            "deal_type": self.deal_type,
            "title": text[:80].strip(),
            "city": city,
            "neighborhood": neighborhood,
            "address": address,
            "rooms": rooms,
            "floor": floor,
            "size_sqm": sqm,
            "price": price,
            "description": text[:200],
            "image_url": img,
            "listing_url": listing_url,
            "property_type": self._extract_prop_type(text),
            "is_new": "חדש" in text,
            "has_parking": "חניה" in text,
            "has_elevator": "מעלית" in text,
            "has_balcony": "מרפסת" in text,
            "has_storage": "מחסן" in text,
            "has_mamad": 'ממ"ד' in text or "ממד" in text,
            "raw_data": {"text": text[:500]},
        }

    @staticmethod
    def _extract_price(text: str) -> Optional[float]:
        m = re.search(r'([\d,]+)\s*₪', text)
        if not m:
            m = re.search(r'(\d{3,}(?:,\d{3})*)', text)
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
    def _extract_sqm(text: str) -> Optional[float]:
        m = re.search(r'([\d,]+)\s*מ"ר', text)
        if m:
            try:
                return float(m.group(1).replace(",", ""))
            except ValueError:
                return None
        return None

    @staticmethod
    def _extract_floor(text: str) -> Optional[int]:
        m = re.search(r'קומה\s*(\d+)', text)
        return int(m.group(1)) if m else None

    @staticmethod
    def _extract_prop_type(text: str) -> str:
        for t in ("דירה", "דירת גן", "פנטהאוז", "קוטג'", "דופלקס", "בית פרטי", "סטודיו"):
            if t in text:
                return t
        return ""

    def __del__(self):
        try:
            if self._session:
                self._session.close()
        except Exception:
            pass
