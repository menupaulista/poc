#!/usr/bin/env python3
"""
Web scraper for doisporum.net offers following SOLID principles.

Setup with uv:
    uv venv
    source .venv/bin/activate  # (Windows: .venv\\Scripts\\activate)
    uv add "httpx[http2]==0.28.1" beautifulsoup4 lxml pandas tqdm

Usage:
    uv run python scraper.py --seed-url "https://doisporum.net/" --max-items 120
"""

import argparse
import asyncio
import json
import logging
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Protocol, Optional, List, Dict, Any
from urllib.parse import urljoin, urlparse

import httpx
import pandas as pd
from bs4 import BeautifulSoup
from tqdm.asyncio import tqdm

# Constants
BASE_URL = "https://doisporum.net"
DETAIL_HREF_PATTERN = r"^/home/details/\d+/?$"
PHONE_PATTERN = r"\(?(\d{2})\)?\s?(\d{4,5})-(\d{4})"
CEP_PATTERN = r"\b\d{5}-\d{3}\b"
ADDRESS_INDICATORS = r"Rua|Av\.?|R\.|Al\.?|Largo|Praça|Praca|Rod\."
OFFER_KEYWORDS = r"^oferta\b|2\s*por\s*1|dois\s*por\s*um|2x1"
PAGINATION_TEXTS = {"próximo", "proximo", "seguinte", "next", "mais"}


# Domain Entities
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


# Protocols (Dependency Inversion)
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


# Implementations
class AsyncHttpxClient:
    """Async HTTP client implementation using httpx."""

    def __init__(
        self,
        timeout: float = 20.0,
        rate_limit_seconds: float = 0.8,
        user_agent: Optional[str] = None,
    ):
        self.timeout = timeout
        self.rate_limit_seconds = rate_limit_seconds
        self.user_agent = (
            user_agent
            or "Mozilla/5.0 (compatible; OfferScraper/1.0; +contact@example.com)"
        )
        self._last_request_time = 0.0

    async def get_text(self, url: str) -> Optional[str]:
        """Fetch HTML content from URL with retries and rate limiting."""
        await self._apply_rate_limit()

        headers = {"User-Agent": self.user_agent}

        for attempt in range(3):  # Up to 3 retries
            try:
                async with httpx.AsyncClient(
                    timeout=self.timeout, follow_redirects=True, http2=True
                ) as client:
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()
                    return response.text

            except Exception as e:
                logging.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < 2:  # Don't sleep after last attempt
                    await asyncio.sleep(1 + attempt)  # Linear backoff

        logging.error(f"Failed to fetch {url} after 3 attempts")
        return None

    async def _apply_rate_limit(self):
        """Apply rate limiting between requests."""
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        if elapsed < self.rate_limit_seconds:
            await asyncio.sleep(self.rate_limit_seconds - elapsed)
        self._last_request_time = time.time()


class DoisPorUmListPageParser:
    """Parser for doisporum.net list pages."""

    def extract_detail_links(self, html: str) -> List[str]:
        """Extract detail page links matching the pattern."""
        soup = BeautifulSoup(html, "lxml")
        links = []

        for link in soup.find_all("a", href=True):
            href = link["href"]
            if re.match(DETAIL_HREF_PATTERN, href):
                absolute_url = urljoin(BASE_URL, href)
                links.append(absolute_url)

        return list(set(links))  # Deduplicate

    def extract_pagination_links(self, html: str) -> List[str]:
        """Extract pagination links using multiple heuristics."""
        soup = BeautifulSoup(html, "lxml")
        pagination_links = []

        # Strategy 1: a[rel="next"] and link[rel="next"]
        for selector in ['a[rel="next"]', 'link[rel="next"]']:
            for link in soup.select(selector):
                href = link.get("href")
                if href:
                    pagination_links.append(urljoin(BASE_URL, href))

        # Strategy 2: anchors with pagination text
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True).lower()
            if any(keyword in text for keyword in PAGINATION_TEXTS):
                href = link["href"]
                pagination_links.append(urljoin(BASE_URL, href))

        return list(set(pagination_links))  # Deduplicate


class DoisPorUmDetailParser:
    """Parser for doisporum.net detail pages."""

    def parse(self, html: str, url: str) -> Optional[OfferItem]:
        """Parse detail page and extract offer information."""
        soup = BeautifulSoup(html, "lxml")

        # Extract ID from URL
        id_match = re.search(r"/details/(\d+)", url)
        offer_id = id_match.group(1) if id_match else None

        # Extract all text blocks
        blocks = self._extract_text_blocks(soup)

        offer = OfferItem(
            id=offer_id,
            url=url,
            title=self._extract_title(soup),
            offer=self._extract_offer(blocks),
            description=self._extract_description(blocks),
            address=self._extract_address(blocks),
            phone=self._extract_phone(blocks, html),
            website=self._extract_website(soup),
            images=self._extract_images(soup),
        )

        return offer

    def _extract_text_blocks(self, soup: BeautifulSoup) -> List[str]:
        """Extract and normalize text blocks from p, li, div elements."""
        blocks = []
        for tag in soup.find_all(["p", "li", "div"]):
            text = tag.get_text(strip=True)
            if text and len(text) > 10:  # Filter out very short texts
                # Normalize whitespace
                normalized = re.sub(r"\s+", " ", text)
                blocks.append(normalized)

        # Also get text from other elements that might contain useful info
        for tag in soup.find_all(["span", "h3", "h4", "h5", "h6"]):
            text = tag.get_text(strip=True)
            if text and len(text) > 10:
                normalized = re.sub(r"\s+", " ", text)
                blocks.append(normalized)

        return list(set(blocks))  # Remove duplicates

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract title using priority order."""
        # Priority: h1 > h2 > [data-testid*="title"] > [class*="title"] > <title>
        selectors = [
            "h1",
            "h2",
            '[data-testid*="title" i]',
            '[class*="title" i]',
            "title",
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)

        return ""

    def _extract_offer(self, blocks: List[str]) -> str:
        """Extract offer text using pattern matching."""
        offer_candidates = []

        for block in blocks:
            # First priority: starts with "Oferta"
            if re.match(r"^oferta\b", block, re.IGNORECASE):
                offer_candidates.append(block)

        if offer_candidates:
            # Return shortest offer text (likely cleaner)
            return min(offer_candidates, key=len)

        # Second priority: contains offer keywords
        for block in blocks:
            if re.search(OFFER_KEYWORDS, block, re.IGNORECASE):
                offer_candidates.append(block)

        if offer_candidates:
            return min(offer_candidates, key=len)

        return ""

    def _extract_description(self, blocks: List[str]) -> str:
        """Extract description - first long block not starting with 'Oferta'."""
        long_blocks = []

        for block in blocks:
            if (
                len(block) > 120
                and not re.match(r"^oferta\b", block, re.IGNORECASE)
                and not re.search(OFFER_KEYWORDS, block, re.IGNORECASE)
            ):
                long_blocks.append(block)

        if long_blocks:
            # Return the longest clean description
            return max(long_blocks, key=len)

        # Fallback: largest non-offer block
        non_offer_blocks = []
        for block in blocks:
            if not re.match(r"^oferta\b", block, re.IGNORECASE) and not re.search(
                OFFER_KEYWORDS, block, re.IGNORECASE
            ):
                non_offer_blocks.append(block)

        if non_offer_blocks:
            return max(non_offer_blocks, key=len)

        return ""

    def _extract_address(self, blocks: List[str]) -> str:
        """Extract address - collect all addresses when multiple locations exist."""

        # First priority: blocks with CEP
        cep_blocks = []
        for block in blocks:
            if re.search(CEP_PATTERN, block):
                # Filter blocks that are clean individual addresses (not long mixed content)
                if len(block) < 150:  # Relaxed limit to include shopping centers
                    cep_blocks.append(block)

        # If we have multiple short CEP blocks, combine them
        if len(cep_blocks) > 1:
            # Remove duplicates and sort by length (shorter = cleaner)
            unique_addresses = []
            seen_addresses = set()

            for addr in cep_blocks:
                # Simple deduplication - check if core address is already included
                core_addr = re.sub(r"^[A-Z\s]+:", "", addr)  # Remove location prefixes
                if core_addr not in seen_addresses:
                    unique_addresses.append(addr)
                    seen_addresses.add(core_addr)

            unique_addresses.sort(key=len)
            return " | ".join(unique_addresses[:5])  # Allow up to 5 addresses
        elif len(cep_blocks) == 1:
            return cep_blocks[0]

        # Fallback: look for address indicators
        address_blocks = []
        for block in blocks:
            if (
                re.search(ADDRESS_INDICATORS, block, re.IGNORECASE) and len(block) < 150
            ):  # Consistent limit
                address_blocks.append(block)

        if address_blocks:
            unique_addresses = list(set(address_blocks))
            unique_addresses.sort(key=len)
            return " | ".join(unique_addresses[:3])

        return ""

    def _extract_phone(self, blocks: List[str], html: str) -> str:
        """Extract phone - collect all phones when multiple locations exist."""
        phone_candidates = set()

        # First try to find phones in address-related blocks
        address_blocks = []
        for block in blocks:
            if re.search(CEP_PATTERN, block) or re.search(
                ADDRESS_INDICATORS, block, re.IGNORECASE
            ):
                address_blocks.append(block)

        # Extract phones from address blocks
        for block in address_blocks:
            matches = re.findall(PHONE_PATTERN, block)
            for match in matches:
                formatted_phone = f"({match[0]}) {match[1]}-{match[2]}"
                phone_candidates.add(formatted_phone)

        # If we found phones in addresses, return them
        if phone_candidates:
            return " | ".join(sorted(phone_candidates))

        # Fallback: search entire page for any phone
        matches = re.findall(PHONE_PATTERN, html)
        for match in matches:
            formatted_phone = f"({match[0]}) {match[1]}-{match[2]}"
            phone_candidates.add(formatted_phone)

        if phone_candidates:
            return " | ".join(sorted(phone_candidates))

        return ""

    def _extract_website(self, soup: BeautifulSoup) -> str:
        """Extract first external website link."""
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.startswith(("http://", "https://")) and "doisporum.net" not in href:
                return href
        return ""

    def _extract_images(self, soup: BeautifulSoup) -> List[str]:
        """Extract and normalize image URLs."""
        images = set()

        for img in soup.find_all("img"):
            # Prefer srcset (last URL is typically highest quality)
            srcset = img.get("srcset")
            if srcset:
                # Parse srcset and get the last (highest quality) URL
                urls = [url.strip().split()[0] for url in srcset.split(",")]
                if urls:
                    image_url = urls[-1]
                else:
                    continue
            else:
                image_url = img.get("src")

            if image_url:
                absolute_url = urljoin(BASE_URL, image_url)
                images.add(absolute_url)

        return list(images)


class PandasOfferRepository:
    """Repository implementation using pandas for persistence."""

    def save_csv(self, items: List[OfferItem], path: str) -> None:
        """Save offers to CSV file."""
        if not items:
            logging.warning("No items to save to CSV")
            return

        data = []
        for item in items:
            item_dict = asdict(item)
            # Add special columns for images
            item_dict["images"] = ",".join(item.images) if item.images else ""
            item_dict["images_json"] = json.dumps(item.images)
            data.append(item_dict)

        df = pd.DataFrame(data)
        df.to_csv(path, index=False)
        logging.info(f"Saved {len(items)} items to {path}")

    def save_jsonl(self, items: List[OfferItem], path: str) -> None:
        """Save offers to JSONL file."""
        if not items:
            logging.warning("No items to save to JSONL")
            return

        with open(path, "w", encoding="utf-8") as f:
            for item in items:
                json.dump(asdict(item), f, ensure_ascii=False)
                f.write("\n")

        logging.info(f"Saved {len(items)} items to {path}")


# Services / Use Cases
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

    list_parser = DoisPorUmListPageParser()
    detail_parser = DoisPorUmDetailParser()
    repository = PandasOfferRepository()

    link_collector = LinkCollector(http_client, list_parser)
    detail_scraper = DetailScraper(http_client, detail_parser, args.max_concurrency)

    coordinator = ScrapeCoordinator(link_collector, detail_scraper, repository)

    # Run the scraping process
    await coordinator.run(
        seed_url=args.seed_url,
        max_items=args.max_items,
        csv_path=args.csv_path,
        jsonl_path=args.jsonl_path,
    )


if __name__ == "__main__":
    asyncio.run(main())
