"""Protocol definitions for dependency inversion."""

from typing import Protocol, Optional, List

from src.models.offer import OfferItem


class HttpClient(Protocol):
    """Protocol for HTTP client operations."""

    async def get_text(self, url: str) -> Optional[str]:
        """Fetch HTML content from URL."""
        ...


class OfferRepository(Protocol):
    """Protocol for persisting offers."""

    def save_csv(self, items: List[OfferItem], path: str) -> None:
        """Save offers to CSV file."""
        ...

    def save_jsonl(self, items: List[OfferItem], path: str) -> None:
        """Save offers to JSONL file."""
        ...
