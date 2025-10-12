from abc import ABC, abstractmethod
from typing import Protocol, Optional, List

from poc.src.models.offer import OfferItem


class PageScrapper(ABC):

    @abstractmethod
    async def collect_detail_urls(self, seed_url: str, max_items: int) -> List[str]:
        ...

    @abstractmethod
    async def fetch_offers(self, detail_urls: List[str], max_concurrency: int = 3) -> List[OfferItem]:
        ...


class DetailParser(Protocol):
    """Protocol for parsing detail pages."""

    def parse(self, html: str, url: str) -> Optional[OfferItem]:
        """Parse HTML content and extract offer details."""
        ...


class ListPageParser(Protocol):
    """Protocol for parsing list pages."""

    def extract_detail_links(self, html: str) -> List[str]:
        """Extract detail page links from list page."""
        ...

    def extract_pagination_links(self, html: str) -> List[str]:
        """Extract pagination links from list page."""
        ...
