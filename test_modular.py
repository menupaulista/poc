#!/usr/bin/env python3
"""Test script to verify the modularized scraper works correctly."""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.clients.httpx_client import AsyncHttpxClient
from poc.src.app.partners.doisporum.list_parser import DoisPorUmListPageParser
from poc.src.app.partners.doisporum.detail_parser import DoisPorUmDetailParser
from src.repositories.pandas_repository import PandasOfferRepository
from src.services.link_collector import LinkCollector
from src.services.detail_scraper import DetailScraper
from src.services.coordinator import ScrapeCoordinator


async def test_modular_scraper():
    """Test the modular scraper with a small number of items."""
    print("Testing modular scraper...")

    # Setup components
    http_client = AsyncHttpxClient(rate_limit_seconds=0.5)
    list_parser = DoisPorUmListPageParser()
    detail_parser = DoisPorUmDetailParser()
    repository = PandasOfferRepository()

    link_collector = LinkCollector(http_client, list_parser)
    detail_scraper = DetailScraper(http_client, detail_parser, max_concurrency=3)
    coordinator = ScrapeCoordinator(link_collector, detail_scraper, repository)

    # Test with small number of items
    await coordinator.run(
        seed_url="https://doisporum.net/",
        max_items=5,
        csv_path="test_modular.csv",
        jsonl_path="test_modular.jsonl",
    )

    print("✅ Modular scraper test completed!")


if __name__ == "__main__":
    asyncio.run(test_modular_scraper())
