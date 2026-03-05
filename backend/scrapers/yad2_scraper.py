"""
Yad2 HTML scraper - uses requests + BeautifulSoup as fallback.
Supports both sale and rent.
"""
import re
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup
from loguru import logger

from scrapers.base_scraper import BaseScraper
from scrapers.city_codes import CITY_TO_YAD2_CODE

YAD2_BASE_URLS = {
    "sale": "https://www.yad2.co.il/realestate/forsale",
    "rent": "https://www.yad2.co.il/realestate/rent",
}


class Yad2Scraper(BaseScraper):
    SOURCE_NAME = "yad2_html"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "he-IL,he;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def __init__(self, deal_type: str = "sale", delay: float = 2.0):
        super().__init__(deal_type=deal_type)
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.delay = delay
        self.base_url = YAD2_BASE_URLS.get(deal_type, YAD2_BASE_URLS["sale"])

    def search(self, city: str, rooms_min: int = 1, rooms_max: int = 8,
               price_max: Optional[float] = None, page: int = 1) -> list[dict]:
        city_code = CITY_TO_YAD2_CODE.get(city)
        if not city_code:
            logger.warning(f"[yad2_html] Unknown city: {city}")
            return []

        params = {
            "city": city_code,
            "rooms": f"{rooms_min}-{rooms_max}",
            "page": page,
        }
        if price_max:
            params["price"] = f"0-{int(price_max)}"

        try:
            time.sleep(self.delay)
            resp = self.session.get(self.base_url, params=params, timeout=30)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"[yad2_html] Request failed for {city}: {e}")
            return []

        return self._parse_listings(resp.text, city)

    def _parse_listings(self, html: str, city: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        properties = []

        feed_items = soup.select("[class*='feeditem'], [class*='feed_item'], [class*='listing']")
        if not feed_items:
            feed_items = soup.find_all("div", attrs={"itemid": True})

        for item in feed_items:
            try:
                prop = self._extract_property(item, city)
                if prop and prop.get("price"):
                    properties.append(prop)
            except Exception as e:
                logger.debug(f"[yad2_html] Failed to parse item: {e}")
                continue

        return properties

    def _extract_property(self, item, city: str) -> Optional[dict]:
        item_id = item.get("itemid") or item.get("data-id") or item.get("id", "")

        title_el = item.select_one("[class*='title'], h2, h3")
        title = title_el.get_text(strip=True) if title_el else ""

        price_el = item.select_one("[class*='price']")
        price_text = price_el.get_text(strip=True) if price_el else ""
        price = self._parse_price(price_text)

        rooms_el = item.select_one("[class*='rooms'], [class*='Rooms']")
        rooms_text = rooms_el.get_text(strip=True) if rooms_el else ""
        rooms = self._parse_number(rooms_text)

        floor_el = item.select_one("[class*='floor'], [class*='Floor']")
        floor_text = floor_el.get_text(strip=True) if floor_el else ""
        floor = self._parse_number(floor_text)

        size_el = item.select_one("[class*='square'], [class*='Square'], [class*='size']")
        size_text = size_el.get_text(strip=True) if size_el else ""
        size = self._parse_number(size_text)

        address_el = item.select_one("[class*='subtitle'], [class*='address']")
        address = address_el.get_text(strip=True) if address_el else ""

        link_el = item.select_one("a[href]")
        link = link_el["href"] if link_el else ""
        if link and not link.startswith("http"):
            link = f"https://www.yad2.co.il{link}"

        img_el = item.select_one("img[src]")
        img = img_el["src"] if img_el else ""

        if not price:
            return None

        return {
            "source": self.SOURCE_NAME,
            "source_id": str(item_id) if item_id else None,
            "deal_type": self.deal_type,
            "title": title,
            "city": city,
            "address": address,
            "rooms": rooms,
            "floor": floor,
            "size_sqm": size,
            "price": price,
            "listing_url": link,
            "image_url": img,
            "raw_data": {"html_snippet": str(item)[:500]},
        }

    @staticmethod
    def _parse_price(text: str) -> Optional[float]:
        if not text:
            return None
        digits = re.sub(r"[^\d]", "", text)
        return float(digits) if digits else None

    @staticmethod
    def _parse_number(text: str) -> Optional[float]:
        if not text:
            return None
        match = re.search(r"[\d.]+", text)
        return float(match.group()) if match else None
