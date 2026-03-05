"""
URL builder for Legacy.com obituary listing pages.

Constructs listing URLs from market config entries in markets.json.
Legacy.com URL pattern (2026):
  County: https://www.legacy.com/us/obituaries/local/{state}/{county-slug}
  City:   https://www.legacy.com/us/obituaries/local/{state}/{city-slug}
"""

# Base URL for Legacy.com local obituary listings
LEGACY_BASE_URL = "https://www.legacy.com/us/obituaries/local"


def build_listing_url(market):
    """
    Build a Legacy.com listing URL from a market config dict.

    Args:
        market: Dict with keys 'state' and 'legacy_slug'.
                Example: {"state": "texas", "legacy_slug": "brown-county"}

    Returns:
        Full Legacy.com listing URL string.

    Raises:
        ValueError: If market is missing required keys.
    """
    state = market.get("state") or ""
    slug = market.get("legacy_slug") or ""

    if not state or not slug:
        raise ValueError(
            f"Market must have 'state' and 'legacy_slug': {market}"
        )

    # Normalize to lowercase for consistent URL construction
    state = state.strip().lower()
    slug = slug.strip().lower()

    return f"{LEGACY_BASE_URL}/{state}/{slug}"


def build_all_urls(markets):
    """
    Build listing URLs for all markets.

    Args:
        markets: List of market dicts from markets.json.

    Returns:
        List of (market_dict, url_string) tuples.
    """
    results = []
    for market in markets:
        url = build_listing_url(market)
        results.append((market, url))
    return results
