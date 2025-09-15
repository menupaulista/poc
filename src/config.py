"""Configuration constants for the scraper."""

# Base URL and patterns
BASE_URL = "https://doisporum.net"
DETAIL_HREF_PATTERN = r"^/home/details/\d+/?$"

# Extraction patterns
PHONE_PATTERN = r"\(?(\d{2})\)?\s?(\d{4,5})-(\d{4})"
CEP_PATTERN = r"\b\d{5}-\d{3}\b"
ADDRESS_INDICATORS = r"Rua|Av\.?|R\.|Al\.?|Largo|Praça|Praca|Rod\."
OFFER_KEYWORDS = r"^oferta\b|2\s*por\s*1|dois\s*por\s*um|2x1"

# Pagination keywords
PAGINATION_TEXTS = {"próximo", "proximo", "seguinte", "next", "mais"}
