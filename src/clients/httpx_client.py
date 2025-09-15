"""HTTP client implementation using httpx."""

import asyncio
import logging
import time
from typing import Optional

import httpx


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
