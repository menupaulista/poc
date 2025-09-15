"""Protocol definitions for dependency inversion."""

from typing import Protocol, Optional, List
from src.models.offer import OfferItem


class HttpClient(Protocol):
    """Protocol for HTTP client operations."""

    async def get_text(self, url: str) -> Optional[str]:
        """Fetch HTML content from URL."""
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


class OfferRepository(Protocol):
    """Protocol for persisting offers."""

    def save_csv(self, items: List[OfferItem], path: str) -> None:
        """Save offers to CSV file."""
        ...

    def save_jsonl(self, items: List[OfferItem], path: str) -> None:
        """Save offers to JSONL file."""
        ...
