"""
WinWin.co.il scraper — uses curl_cffi (chrome120 TLS fingerprint).
Retries up to 3 times with exponential back-off on failure.
"""
import json
import random
import re
import time
from typing import Optional

from loguru import logger

from scrapers._http import browser_headers, random_ua
from scrapers.base_scraper import BaseScraper

DEAL_PATHS = {"sale": "ForSale", "rent": "ForRent"}
_TIMEOUT = 15
_MAX_ATTEMPTS = 2


class WinWinScraper(BaseScraper):
    SOURCE_NAME = "winwin"
    BASE_URL = "https://www.winwin.co.il"

    def __init__(self, deal_type: str = "sale", delay: float = 3.0):
        super().__init__(deal_type=deal_type)
        self.delay = delay
        self.deal_path = DEAL_PATHS.get(deal_type, "ForSale")
        self._session = None

    # ------------------------------------------------------------------
    # Session: fresh TLS fingerprint + browser headers on every new session
    # ------------------------------------------------------------------

    def _make_session(self):
        from curl_cffi import requests as curl_requests
        ua = random_ua()
        session = curl_requests.Session(impersonate="chrome120")
        session.headers.update(browser_headers(ua))
        return session

    @property
    def session(self):
        if self._session is None:
            self._session = self._make_session()
        return self._session

    # ------------------------------------------------------------------
    # Public search — with exponential back-off retry
    # ------------------------------------------------------------------

    def search(self, city: str, rooms_min: int = 1, rooms_max: int = 8,
               price_max: Optional[float] = None, page: int = 1) -> list[dict]:

        url = f"{self.BASE_URL}/RealEstate/{self.deal_path}/Apartments.aspx"
        params = {
            "sText": city,
            "iRoomsMin": rooms_min,
            "iRoomsMax": rooms_max,
            "iPage": page,
        }
        if price_max:
            params["iPriceMax"] = int(price_max)

        for attempt in range(_MAX_ATTEMPTS):
            # Human-like base delay + exponential back-off on retries
            wait = random.uniform(3, 7) + (2 ** attempt - 1)
            time.sleep(wait)

            try:
                resp = self.session.get(url, params=params, timeout=_TIMEOUT)

                if resp.status_code != 200:
                    logger.warning(
                        f"[winwin] HTTP {resp.status_code} for {city} "
                        f"(attempt {attempt + 1}/{_MAX_ATTEMPTS})"
                    )
                    self._session = None
                    continue

                content_type = resp.headers.get("content-type", "")
                if "json" in content_type:
                    try:
                        return self._parse_json(resp.json(), city)
                    except Exception:
                        pass
                return self._parse_html(resp.text, city)

            except Exception as e:
                err_str = str(e).lower()
                if "timeout" in err_str or "timed out" in err_str:
                    logger.warning(
                        f"[winwin] Timeout for {city} (attempt {attempt + 1}/{_MAX_ATTEMPTS})"
                    )
                else:
                    logger.warning(
                        f"[winwin] Request failed for {city} "
                        f"(attempt {attempt + 1}/{_MAX_ATTEMPTS}): {e}"
                    )
                self._session = None  # fresh session/UA on each retry

        logger.error(f"[winwin] All {_MAX_ATTEMPTS} attempts failed for {city}")
        return []

    # ------------------------------------------------------------------
    # JSON response parsing
    # ------------------------------------------------------------------

    def _parse_json(self, data, city: str) -> list[dict]:
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("items", []) or data.get("results", []) or data.get("data", [])
        else:
            return []

        properties = []
        for item in items:
            try:
                prop = self._normalize_json(item, city)
                if prop:
                    properties.append(prop)
            except Exception:
                continue

        if properties:
            logger.info(f"[winwin] JSON: {len(properties)} listings for {city}")
        return properties

    def _normalize_json(self, raw: dict, city: str) -> Optional[dict]:
        price = raw.get("price") or raw.get("Price")
        try:
            price = float(str(price).replace(",", "").replace("₪", ""))
        except (ValueError, TypeError):
            return None
        if not price or price < 1000:
            return None

        rooms = raw.get("rooms") or raw.get("Rooms")
        try:
            rooms = float(rooms) if rooms else None
        except (ValueError, TypeError):
            rooms = None

        floor = raw.get("floor") or raw.get("Floor")
        try:
            floor = int(floor) if floor is not None else None
        except (ValueError, TypeError):
            floor = None

        sqm = raw.get("squareMeters") or raw.get("SquareMeters") or raw.get("size")
        try:
            sqm = float(sqm) if sqm else None
        except (ValueError, TypeError):
            sqm = None

        item_id = raw.get("id") or raw.get("Id")
        address = raw.get("address") or raw.get("Address") or ""
        title = raw.get("title") or raw.get("Title") or address

        link = raw.get("url") or raw.get("Url") or ""
        if link and not link.startswith("http"):
            link = f"{self.BASE_URL}{link}"

        raw_str = str(raw)
        return {
            "source": self.SOURCE_NAME,
            "source_id": str(item_id) if item_id else None,
            "deal_type": self.deal_type,
            "title": title,
            "city": city,
            "address": address,
            "rooms": rooms,
            "floor": floor,
            "size_sqm": sqm,
            "price": price,
            "listing_url": link,
            "has_parking": "חניה" in raw_str,
            "has_elevator": "מעלית" in raw_str,
            "has_balcony": "מרפסת" in raw_str,
            "has_storage": "מחסן" in raw_str,
            "has_mamad": 'ממ"ד' in raw_str or "ממד" in raw_str,
            "raw_data": raw,
        }

    # ------------------------------------------------------------------
    # HTML response parsing
    # ------------------------------------------------------------------

    def _parse_html(self, html: str, city: str) -> list[dict]:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        properties = []

        cards = soup.select(
            ".listing-item, .property-item, .result-item, "
            "[class*='listing'], [class*='property'], [class*='result'], "
            "tr[class*='item'], div[class*='ad-item']"
        )

        for card in cards[:30]:
            try:
                prop = self._extract_card(card, city)
                if prop and prop.get("price"):
                    properties.append(prop)
            except Exception:
                continue

        if properties:
            logger.info(f"[winwin] HTML: {len(properties)} listings for {city}")
        return properties

    def _extract_card(self, card, city: str) -> Optional[dict]:
        price_el = card.select_one("[class*='price']")
        if not price_el:
            return None
        price_text = re.sub(r"[^\d]", "", price_el.get_text())
        if not price_text:
            return None
        price = float(price_text)
        if price < 1000:
            return None

        title_el = card.select_one("[class*='title'], h2, h3")
        title = title_el.get_text(strip=True) if title_el else ""

        rooms_el = card.select_one("[class*='room']")
        rooms = None
        if rooms_el:
            m = re.search(r"[\d.]+", rooms_el.get_text())
            rooms = float(m.group()) if m else None

        address_el = card.select_one("[class*='address'], [class*='location']")
        address = address_el.get_text(strip=True) if address_el else ""

        link_el = card.select_one("a[href]")
        link = ""
        if link_el:
            link = link_el.get("href", "")
            if link and not link.startswith("http"):
                link = f"{self.BASE_URL}{link}"

        item_id = card.get("data-id") or card.get("id") or ""
        text = card.get_text()

        return {
            "source": self.SOURCE_NAME,
            "source_id": str(item_id) if item_id else None,
            "deal_type": self.deal_type,
            "title": title,
            "city": city,
            "address": address,
            "rooms": rooms,
            "price": price,
            "listing_url": link,
            "has_parking": "חניה" in text,
            "has_elevator": "מעלית" in text,
            "has_balcony": "מרפסת" in text,
            "has_storage": "מחסן" in text,
            "has_mamad": 'ממ"ד' in text or "ממד" in text,
            "raw_data": {"html": str(card)[:300]},
        }

    def __del__(self):
        try:
            if getattr(self, "_session", None):
                self._session.close()
        except Exception:
            pass
