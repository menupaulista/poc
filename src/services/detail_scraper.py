"""Service for scraping detail pages with concurrency control."""

import asyncio
from typing import List, Optional

from tqdm.asyncio import tqdm

from src.models.offer import OfferItem
from src.protocols.base import HttpClient, DetailParser


class DetailScraper:
    """Service for scraping detail pages with concurrency control."""

    def __init__(
        self,
        http_client: HttpClient,
        detail_parser: DetailParser,
        max_concurrency: int = 6,
    ):
        self.http_client = http_client
        self.detail_parser = detail_parser
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def scrape_details(self, urls: List[str]) -> List[OfferItem]:
        """Scrape detail pages with concurrency control."""
        tasks = [self._scrape_single_detail(url) for url in urls]

        results = []
        for coro in tqdm.as_completed(tasks, desc="Scraping details"):
            item = await coro
            if item:
                results.append(item)

        return results

    async def _scrape_single_detail(self, url: str) -> Optional[OfferItem]:
        """Scrape a single detail page."""
        async with self.semaphore:
            html = await self.http_client.get_text(url)
            if html:
                return self.detail_parser.parse(html, url)
        return None
