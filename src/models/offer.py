"""Domain entities for the scraper."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class OfferItem:
    """Domain entity representing an offer item."""

    id: Optional[str] = None
    url: str = ""
    title: str = ""
    offer: str = ""
    description: str = ""
    address: str = ""
    phone: str = ""
    website: str = ""
    images: List[str] = None

    def __post_init__(self):
        if self.images is None:
            self.images = []
