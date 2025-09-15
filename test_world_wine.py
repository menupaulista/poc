#!/usr/bin/env python3
"""
Test script to debug the World Wine page extraction.
"""

import asyncio
import httpx
from bs4 import BeautifulSoup
import sys
import os

# Add the current directory to path to import from scraper.py
sys.path.append(os.path.dirname(__file__))
from scraper import DoisPorUmDetailParser, AsyncHttpxClient


async def test_world_wine_page():
    """Test the extraction for the World Wine page specifically."""
    url = "https://doisporum.net/home/details/177"

    # Create HTTP client and parser
    client = AsyncHttpxClient(rate_limit_seconds=0.5)
    parser = DoisPorUmDetailParser()

    print(f"Fetching: {url}")
    html = await client.get_text(url)

    if not html:
        print("Failed to fetch HTML")
        return

    print(f"HTML length: {len(html)}")

    # Parse with our parser
    offer = parser.parse(html, url)

    if offer:
        print("\n=== EXTRACTED DATA ===")
        print(f"ID: {offer.id}")
        print(f"Title: {offer.title}")
        print(f"Offer: {offer.offer}")
        print(f"Description: {offer.description[:200]}...")
        print(f"Address: {offer.address}")
        print(f"Phone: {offer.phone}")
        print(f"Website: {offer.website}")
        print(f"Images: {offer.images}")

    # Let's also debug the text blocks extraction
    soup = BeautifulSoup(html, "lxml")
    blocks = parser._extract_text_blocks(soup)

    print(f"\n=== ALL TEXT BLOCKS ({len(blocks)}) ===")
    for i, block in enumerate(blocks):
        if len(block) > 50:  # Only show longer blocks
            print(f"{i}: {block[:100]}...")

    # Look specifically for address-like blocks
    print(f"\n=== ADDRESS-LIKE BLOCKS ===")
    import re

    CEP_PATTERN = r"\b\d{5}-\d{3}\b"
    ADDRESS_INDICATORS = r"Rua|Av\.?|R\.|Al\.?|Largo|Praça|Praca|Rod\."

    for i, block in enumerate(blocks):
        if re.search(CEP_PATTERN, block) or re.search(
            ADDRESS_INDICATORS, block, re.IGNORECASE
        ):
            print(f"Block {i} (len={len(block)}): {block}")


if __name__ == "__main__":
    asyncio.run(test_world_wine_page())
