#!/usr/bin/env python3
"""
Web scraper for doisporum.net offers following SOLID principles.

Setup with uv:
    uv venv
    source .venv/bin/activate  # (Windows: .venv\\Scripts\\activate)
    uv add "httpx[http2]==0.28.1" beautifulsoup4 lxml pandas tqdm

Usage:
    uv run python main.py --seed-url "https://doisporum.net/" --max-items 120
"""

import argparse
import asyncio
import logging

from poc.src.app.partners.doisporum.parser import DoisPorUmScraper
from src.clients.httpx_client import AsyncHttpxClient
from src.repositories.pandas_repository import PandasOfferRepository
from src.services.coordinator import ScrapeCoordinator


def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Scrape offers from doisporum.net following SOLID principles"
    )

    parser.add_argument("--seed-url", required=True, help="Starting URL for scraping")
    parser.add_argument(
        "--max-items",
        type=int,
        default=120,
        help="Maximum number of items to scrape (default: 120)",
    )
    parser.add_argument(
        "--rate-limit-seconds",
        type=float,
        default=0.8,
        help="Seconds to wait between requests (default: 0.8)",
    )
    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=6,
        help="Maximum concurrent requests (default: 6)",
    )
    parser.add_argument(
        "--csv-path",
        default="doisporum_ofertas.csv",
        help="Path for CSV output (default: doisporum_ofertas.csv)",
    )
    parser.add_argument(
        "--jsonl-path",
        default="doisporum_ofertas.jsonl",
        help="Path for JSONL output (default: doisporum_ofertas.jsonl)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="Request timeout in seconds (default: 20.0)",
    )
    parser.add_argument("--user-agent", help="Custom User-Agent string")

    return parser.parse_args()


async def main():
    """Main entry point - composition root."""
    setup_logging()
    args = parse_args()

    # Dependency injection / composition
    http_client = AsyncHttpxClient(
        timeout=args.timeout,
        rate_limit_seconds=args.rate_limit_seconds,
        user_agent=args.user_agent,
    )

    scraper = DoisPorUmScraper.default(async_http_client=http_client)

    repository = PandasOfferRepository()
    coordinator = ScrapeCoordinator(scraper=scraper, repository=repository)

    # Run the scraping process
    await coordinator.run(
        seed_url=args.seed_url,
        max_items=args.max_items,
        csv_path=args.csv_path,
        jsonl_path=args.jsonl_path,
    )


if __name__ == "__main__":
    asyncio.run(main())
