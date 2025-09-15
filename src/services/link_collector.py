"""Service for collecting detail page links from list pages."""

import logging
from typing import List

from src.protocols.base import HttpClient, ListPageParser


class LinkCollector:
    """Service for collecting detail page links from list pages."""

    def __init__(self, http_client: HttpClient, list_parser: ListPageParser):
        self.http_client = http_client
        self.list_parser = list_parser

    async def collect_links(self, seed_url: str, max_items: int) -> List[str]:
        """Collect detail links using BFS with pagination."""
        collected_links = set()
        visited_pages = set()
        pages_to_visit = [seed_url]

        while pages_to_visit and len(collected_links) < max_items:
            current_url = pages_to_visit.pop(0)

            if current_url in visited_pages:
                continue

            visited_pages.add(current_url)
            logging.info(f"Collecting links from: {current_url}")

            html = await self.http_client.get_text(current_url)
            if not html:
                continue

            # Extract detail links
            detail_links = self.list_parser.extract_detail_links(html)
            for link in detail_links:
                if len(collected_links) >= max_items:
                    break
                collected_links.add(link)

            logging.info(
                f"Found {len(detail_links)} detail links. Total: {len(collected_links)}"
            )

            # If we need more items, follow pagination
            if len(collected_links) < max_items:
                pagination_links = self.list_parser.extract_pagination_links(html)
                for link in pagination_links:
                    if link not in visited_pages:
                        pages_to_visit.append(link)

        result = list(collected_links)[:max_items]
        logging.info(f"Collected {len(result)} detail links total")
        return result
