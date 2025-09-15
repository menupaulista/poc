"""Parser for doisporum.net detail pages."""

import re
from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.config import (
    BASE_URL,
    PHONE_PATTERN,
    CEP_PATTERN,
    ADDRESS_INDICATORS,
    OFFER_KEYWORDS,
)
from src.models.offer import OfferItem


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
