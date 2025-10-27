"""Coordinator that orchestrates the entire scraping process."""

import logging

from poc.src.parsers.base_parser import PageScrapper
from poc.src.protocols.base import OfferRepository


class ScrapeCoordinator:
    """Coordinator that orchestrates the entire scraping process."""

    def __init__(
            self,
            scraper: PageScrapper,
            repository: OfferRepository,
    ):
        self.scraper = scraper
        self.repository = repository

    async def run(self, seed_url: str, max_items: int, csv_path: str, jsonl_path: str):
        """Run the complete scraping process."""
        logging.info("Starting scrape process...")

        # Collect detail links
        detail_urls = await self.scraper.collect_detail_urls(seed_url, max_items)

        if not detail_urls:
            logging.error("No detail URLs collected")
            return

        # Scrape detail pages
        offers = await self.scraper.fetch_offers(detail_urls)

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
