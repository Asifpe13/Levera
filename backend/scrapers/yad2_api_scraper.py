"""
Yad2 scraper — uses curl_cffi for TLS fingerprint impersonation
to bypass ShieldSquare bot protection. Parses __NEXT_DATA__ from
server-rendered HTML.
"""
import json
import re
import time
from typing import Optional

from loguru import logger

from scrapers.base_scraper import BaseScraper
from scrapers.city_codes import CITY_TO_YAD2_CODE, CITY_TO_YAD2_RENT_CODE, YAD2_RENT_TOP_AREA

DEAL_MAP = {"sale": "forsale", "rent": "rent"}


class Yad2ApiScraper(BaseScraper):
    SOURCE_NAME = "yad2"

    def __init__(self, deal_type: str = "sale", delay: float = 3.0):
        super().__init__(deal_type=deal_type)
        self.delay = delay
        self.deal_slug = DEAL_MAP.get(deal_type, "forsale")
        self._session = None

    @property
    def session(self):
        if self._session is None:
            from curl_cffi import requests as curl_requests
            self._session = curl_requests.Session(impersonate="chrome")
        return self._session

    def search(self, city: str, rooms_min: int = 1, rooms_max: int = 8,
               price_max: Optional[float] = None, page: int = 1) -> list[dict]:
        time.sleep(self.delay)

        is_rent = self.deal_type == "rent"
        city_code = (CITY_TO_YAD2_RENT_CODE if is_rent else CITY_TO_YAD2_CODE).get(city)
        if not city_code:
            logger.debug(f"[yad2/{self.deal_type}] No city code for '{city}', skipping")
            return []

        params: dict = {"city": city_code}
        if rooms_min > 1 or rooms_max < 8:
            if is_rent:
                params["minRooms"] = rooms_min
                params["maxRooms"] = rooms_max
            else:
                params["rooms"] = f"{rooms_min}-{rooms_max}"
        if price_max:
            if is_rent:
                params["minPrice"] = 0
                params["maxPrice"] = int(price_max)
            else:
                params["price"] = f"0-{int(price_max)}"
        if is_rent and city in YAD2_RENT_TOP_AREA:
            params["topArea"] = YAD2_RENT_TOP_AREA[city]
        if page > 1:
            params["page"] = page

        url = f"https://www.yad2.co.il/realestate/{self.deal_slug}"
        try:
            resp = self.session.get(url, params=params)
            if resp.status_code != 200:
                logger.warning(f"[yad2] HTTP {resp.status_code} for {city}")
                return []
        except Exception as e:
            logger.error(f"[yad2] Request failed for {city}: {e}")
            return []

        return self._parse_next_data(resp.text, city)

    def _parse_next_data(self, html: str, city: str) -> list[dict]:
        if "captcha" in html[:2000].lower() or "shieldsquare" in html[:2000].lower():
            logger.warning(f"[yad2] Captcha detected for {city}")
            return []

        match = re.search(
            r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
            html, re.DOTALL,
        )
        if not match:
            logger.debug(f"[yad2] No __NEXT_DATA__ for {city}")
            return []

        try:
            nd = json.loads(match.group(1))
        except json.JSONDecodeError:
            logger.warning(f"[yad2] Bad JSON for {city}")
            return []

        all_items = []
        feed = nd.get("props", {}).get("pageProps", {}).get("feed", {})
        total = feed.get("pagination", {}).get("total", 0)

        for bucket in ("private", "agency", "platinum"):
            all_items.extend(feed.get(bucket, []))

        if not all_items:
            all_items = self._find_feed_items_anywhere(nd)

        if not all_items:
            logger.info(f"[yad2] 0 listings for {city}")
            return []

        properties = []
        for item in all_items:
            prop = self._normalize(item, city)
            if prop:
                properties.append(prop)

        logger.info(f"[yad2] Found {len(properties)} listings for {city} (total on site: {total})")
        return properties

    def _find_feed_items_anywhere(self, obj, depth: int = 0) -> list:
        """Recursively search __NEXT_DATA__ for any list of listing-like objects."""
        if depth > 15:
            return []
        if isinstance(obj, list):
            if obj and isinstance(obj[0], dict):
                first = obj[0]
                if (first.get("token") or first.get("id")) and first.get("price") is not None:
                    return obj
            for child in obj:
                found = self._find_feed_items_anywhere(child, depth + 1)
                if found:
                    return found
        if isinstance(obj, dict):
            for key in ("feed_items", "feedItems", "items", "listings", "results", "private", "agency", "platinum"):
                if key in obj and isinstance(obj[key], list) and obj[key]:
                    first = obj[key][0]
                    if isinstance(first, dict) and (first.get("token") or first.get("id")) and first.get("price") is not None:
                        return obj[key]
            for v in obj.values():
                found = self._find_feed_items_anywhere(v, depth + 1)
                if found:
                    return found
        return []

    def _normalize(self, raw: dict, city: str) -> Optional[dict]:
        token = str(raw.get("token") or raw.get("id") or "").strip()
        if not token:
            return None

        price = raw.get("price")
        if isinstance(price, str):
            price = price.replace(",", "").replace("₪", "").replace(" ", "")
        try:
            price = float(price) if price else None
        except (ValueError, TypeError):
            return None
        min_price = 500 if self.deal_type == "rent" else 1000
        if not price or price < min_price:
            return None

        addr = raw.get("address", {})
        city_name = addr.get("city", {}).get("text", city) if isinstance(addr, dict) else city
        neighborhood = addr.get("neighborhood", {}).get("text", "") if isinstance(addr, dict) else ""
        street = addr.get("street", {}).get("text", "") if isinstance(addr, dict) else ""
        house_num = addr.get("house", {}).get("text", "") if isinstance(addr, dict) else ""
        address = f"{street} {house_num}".strip()

        details = raw.get("additionalDetails", {})
        if isinstance(details, dict):
            rooms = details.get("roomsCount")
            sqm = details.get("squareMeter")
            prop_type = details.get("property", {}).get("text", "") if isinstance(details.get("property"), dict) else ""
        else:
            rooms = None
            sqm = None
            prop_type = ""

        try:
            rooms = float(rooms) if rooms is not None else None
        except (ValueError, TypeError):
            rooms = None

        try:
            sqm = float(sqm) if sqm is not None else None
        except (ValueError, TypeError):
            sqm = None

        meta = raw.get("metaData", {})
        cover_img = meta.get("coverImage", "") if isinstance(meta, dict) else ""

        listing_url = ""
        for key in ("link", "url", "navigation", "row_1_link", "item_link"):
            val = raw.get(key)
            if isinstance(val, str) and val.strip().startswith("http"):
                listing_url = val.strip()
                break
            if isinstance(val, dict) and (val.get("link") or val.get("url")):
                u = (val.get("link") or val.get("url") or "").strip()
                if u.startswith("http"):
                    listing_url = u
                    break
        if not listing_url and token:
            listing_url = f"https://www.yad2.co.il/item/{token}"

        tags_text = " ".join(t.get("name", "") for t in raw.get("tags", []) if isinstance(t, dict))
        combined = tags_text + " " + str(raw.get("additionalDetails", ""))

        return {
            "source": self.SOURCE_NAME,
            "source_id": token,
            "deal_type": self.deal_type,
            "title": f"{prop_type} ב{city_name}" if prop_type else f"נכס ב{city_name}",
            "city": city_name,
            "neighborhood": neighborhood,
            "address": address,
            "rooms": rooms,
            "floor": None,
            "size_sqm": sqm,
            "price": price,
            "description": "",
            "image_url": cover_img,
            "listing_url": listing_url,
            "property_type": prop_type,
            "is_new": False,
            "has_parking": "חניה" in combined,
            "has_elevator": "מעלית" in combined,
            "has_balcony": "מרפסת" in combined,
            "has_storage": "מחסן" in combined,
            "has_mamad": 'ממ"ד' in combined or "ממד" in combined,
            "raw_data": raw,
        }

    def __del__(self):
        try:
            if self._session:
                self._session.close()
        except Exception:
            pass
