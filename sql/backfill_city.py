"""One-time script to backfill city for existing obituaries.

Re-fetches listing pages for each existing market and matches URLs
to populate city from Legacy.com's location.city.fullName JSON field.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.obit_parser import extract_obits_from_listing
from scraper.url_builder import build_listing_url
from scraper.db_writer import get_connection
from utils.rate_limiter import polite_get
from utils.logger import get_logger

log = get_logger(__name__)

MARKETS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config",
    "markets.json",
)

UPDATE_CITY_SQL = "UPDATE obituaries SET city = %s WHERE legacy_url = %s AND (city IS NULL OR city = '')"


def backfill():
    with open(MARKETS_FILE, "r", encoding="utf-8") as f:
        markets = json.load(f)

    # Only process original markets (not the new IL ones)
    original_markets = [m for m in markets if not m["site_id"].startswith("il-")]

    conn = get_connection()
    cursor = conn.cursor()
    total_updated = 0

    try:
        for market in original_markets:
            url = build_listing_url(market)
            log.info("[OK] Fetching listing for %s", market["site_id"])

            resp = polite_get(url)
            if not resp:
                log.warning("[WARN] Failed to fetch %s", url)
                continue

            obits = extract_obits_from_listing(resp.text)
            updated = 0

            for obit in obits:
                city = obit.get("city") or ""
                obit_url = obit.get("url") or ""
                if city and obit_url:
                    cursor.execute(UPDATE_CITY_SQL, (city, obit_url))
                    if cursor.rowcount > 0:
                        updated += 1

            conn.commit()
            total_updated += updated
            if updated > 0:
                log.info("[OK] %s: updated city for %d obits", market["site_id"], updated)

    finally:
        cursor.close()
        conn.close()

    log.info("[OK] Backfill complete: %d obits updated with city", total_updated)


if __name__ == "__main__":
    backfill()
