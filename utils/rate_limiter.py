"""
Rate limiter and polite request helper for Legacy.com scraping.

Enforces 2-second delay between requests and sets a polite User-Agent.
On 429/503, waits 60 seconds and retries once before giving up.
"""

import time

import requests

from utils.logger import get_logger

log = get_logger(__name__)

# Polite scraping constants
REQUEST_DELAY_SECONDS = 2
RETRY_DELAY_SECONDS = 60
MAX_RETRIES = 1
USER_AGENT = "Mozilla/5.0 (compatible; CR-NewsBot/1.0; +https://crcommunity.news)"

# Status codes that trigger a retry after a longer wait
RETRY_STATUS_CODES = {429, 503}

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def polite_get(url, timeout=30):
    """
    Perform a GET request with polite delays and retry logic.

    Waits REQUEST_DELAY_SECONDS before each request. If the server returns
    429 or 503, waits RETRY_DELAY_SECONDS and retries once.

    Args:
        url: The URL to fetch.
        timeout: Request timeout in seconds.

    Returns:
        requests.Response on success, None on failure.
    """
    time.sleep(REQUEST_DELAY_SECONDS)

    for attempt in range(1 + MAX_RETRIES):
        try:
            resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)

            if resp.status_code in RETRY_STATUS_CODES and attempt < MAX_RETRIES:
                log.warning(
                    "[WARN] %d from %s — waiting %ds before retry",
                    resp.status_code,
                    url,
                    RETRY_DELAY_SECONDS,
                )
                time.sleep(RETRY_DELAY_SECONDS)
                continue

            if resp.status_code != 200:
                log.error("[ERR] HTTP %d for %s", resp.status_code, url)
                return None

            return resp

        except requests.RequestException as exc:
            log.error("[ERR] Request failed for %s: %s", url, exc)
            if attempt < MAX_RETRIES:
                log.info("Retrying in %ds...", RETRY_DELAY_SECONDS)
                time.sleep(RETRY_DELAY_SECONDS)
                continue
            return None

    return None
