"""Coordinator that orchestrates the entire scraping process."""

import logging

from src.protocols.base import OfferRepository
from src.services.link_collector import LinkCollector
from src.services.detail_scraper import DetailScraper


class ScrapeCoordinator:
    """Coordinator that orchestrates the entire scraping process."""

    def __init__(
        self,
        link_collector: LinkCollector,
        detail_scraper: DetailScraper,
        repository: OfferRepository,
    ):
        self.link_collector = link_collector
        self.detail_scraper = detail_scraper
        self.repository = repository

    async def run(self, seed_url: str, max_items: int, csv_path: str, jsonl_path: str):
        """Run the complete scraping process."""
        logging.info("Starting scrape process...")

        # Collect detail links
        detail_urls = await self.link_collector.collect_links(seed_url, max_items)

        if not detail_urls:
            logging.error("No detail URLs collected")
            return

        # Scrape detail pages
        offers = await self.detail_scraper.scrape_details(detail_urls)

        if not offers:
            logging.error("No offers scraped")
            return

        # Sort by numeric ID if possible
        def sort_key(offer):
            try:
                return int(offer.id) if offer.id else float("inf")
            except (ValueError, TypeError):
                return float("inf")

        offers.sort(key=sort_key)

        # Save results
        self.repository.save_csv(offers, csv_path)
        self.repository.save_jsonl(offers, jsonl_path)

        logging.info(f"Scraping completed! {len(offers)} offers saved.")
        print(f"\n🎉 Success! Scraped {len(offers)} offers")
        print(f"📄 CSV saved to: {csv_path}")
        print(f"📝 JSONL saved to: {jsonl_path}")
