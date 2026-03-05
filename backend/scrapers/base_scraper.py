from abc import ABC, abstractmethod
from typing import Optional
from loguru import logger


class BaseScraper(ABC):
    """Base class for all real estate scrapers."""

    SOURCE_NAME: str = "unknown"

    def __init__(self, deal_type: str = "sale"):
        """deal_type: 'sale' or 'rent'"""
        self.deal_type = deal_type

    @abstractmethod
    def search(self, city: str, rooms_min: int = 1, rooms_max: int = 8,
               price_max: Optional[float] = None, page: int = 1) -> list[dict]:
        pass

    def search_all_cities(self, cities: list[str], rooms_min: int = 1,
                          rooms_max: int = 8, price_max: Optional[float] = None,
                          max_pages: int = 3) -> list[dict]:
        all_properties = []
        for city in cities:
            for page in range(1, max_pages + 1):
                try:
                    results = self.search(city, rooms_min, rooms_max, price_max, page)
                    if not results:
                        break
                    all_properties.extend(results)
                    logger.info(
                        f"[{self.SOURCE_NAME}/{self.deal_type}] "
                        f"{city} page {page}: {len(results)} properties"
                    )
                except Exception as e:
                    logger.error(
                        f"[{self.SOURCE_NAME}/{self.deal_type}] "
                        f"Error scraping {city} page {page}: {e}"
                    )
                    break
        return all_properties
