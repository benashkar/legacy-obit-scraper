"""
Main Legacy.com obituary scraper.

Class LegacyScraper takes a market config dict and scrapes today's obituaries.
Uses polite rate limiting (2s between requests, one market at a time).
"""

from bs4 import BeautifulSoup

from scraper.obit_parser import (
    extract_obits_from_listing,
    parse_funeral_home,
    parse_name,
    parse_dates,
    parse_obit_text,
    split_name,
)
from scraper.url_builder import build_listing_url
from scraper.db_writer import url_exists
from utils.logger import get_logger
from utils.rate_limiter import polite_get

log = get_logger(__name__)


class LegacyScraper:
    """
    Scraper for a single Legacy.com market.

    Fetches the listing page, extracts obit links, then fetches each
    individual obituary page for full details.

    Args:
        market: Dict from markets.json with keys site_id, state, legacy_slug, type.
        conn: MySQL connection (used to skip already-scraped URLs).
    """

    def __init__(self, market, conn=None):
        """
        Initialize the scraper for a specific market.

        Args:
            market: Market config dict from markets.json.
            conn: Optional MySQL connection for URL dedup checks.
        """
        self.market = market
        self.site_id = market.get("site_id") or ""
        self.conn = conn
        self.listing_url = build_listing_url(market)

    def scrape_today(self):
        """
        Scrape today's obituaries for this market.

        1. Fetches the listing page
        2. Extracts obit entries (JSON or HTML)
        3. For each new URL, fetches the full obit page for complete data
        4. Returns list of fully-populated obit dicts

        Returns:
            List of obit dicts ready for db_writer.upsert_obit().
            Each dict has: url, deceased_name, first_name, middle_name,
            last_name, name_suffix, obit_text, published_date, death_date,
            funeral_home.
        """
        log.info("[OK] Scraping %s — %s", self.site_id, self.listing_url)

        # Step 1: Fetch the listing page
        resp = polite_get(self.listing_url)
        if not resp:
            log.error("[ERR] Failed to fetch listing for %s", self.site_id)
            return []

        # Step 2: Extract obit entries from listing page
        obits = extract_obits_from_listing(resp.text)
        log.info("[OK] Found %d obituaries on listing for %s", len(obits), self.site_id)

        if not obits:
            return []

        # Step 3: For each obit, check if we already have it, then fetch full page
        results = []
        for obit in obits:
            url = obit.get("url") or ""
            if not url:
                continue

            # Skip if already in DB
            if self.conn and url_exists(self.conn, url):
                log.info("[--] Already scraped: %s", url)
                continue

            # If listing data is already complete (from JSON), use it directly
            if obit.get("obit_text"):
                results.append(obit)
                continue

            # Fetch the full obit page for complete data
            enriched = self._fetch_full_obit(url, obit)
            if enriched:
                results.append(enriched)

        log.info(
            "[OK] %s: %d total on page, %d new to process",
            self.site_id,
            len(obits),
            len(results),
        )
        return results

    def _fetch_full_obit(self, url, partial_obit):
        """
        Fetch an individual obituary page and extract full details.

        Merges data from the full page with any partial data from the listing.

        Args:
            url: Full obituary page URL.
            partial_obit: Partial obit dict from listing extraction.

        Returns:
            Fully-populated obit dict, or None on failure.
        """
        resp = polite_get(url)
        if not resp:
            log.warning("[WARN] Failed to fetch obit page: %s", url)
            return partial_obit  # Return partial data rather than nothing

        soup = BeautifulSoup(resp.text, "lxml")

        # Extract fields from the full page
        name = parse_name(soup) or partial_obit.get("deceased_name") or ""
        dates = parse_dates(soup)
        funeral_home = parse_funeral_home(soup) or partial_obit.get("funeral_home")
        obit_text = parse_obit_text(soup) or partial_obit.get("obit_text") or ""

        parsed_name = split_name(name)

        return {
            "url": url,
            "deceased_name": name,
            "first_name": parsed_name["first_name"],
            "middle_name": parsed_name["middle_name"],
            "last_name": parsed_name["last_name"],
            "name_suffix": parsed_name["name_suffix"],
            "obit_text": obit_text,
            "published_date": dates.get("published") or partial_obit.get("published_date"),
            "death_date": dates.get("death") or partial_obit.get("death_date"),
            "birth_date": partial_obit.get("birth_date"),
            "funeral_home": funeral_home,
            "city": partial_obit.get("city") or "",
            "state": partial_obit.get("state") or "",
        }
