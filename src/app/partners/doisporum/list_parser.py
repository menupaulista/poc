"""Parser for doisporum.net list pages."""

import re
from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from poc.src.config import BASE_URL, DETAIL_HREF_PATTERN, PAGINATION_TEXTS


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
