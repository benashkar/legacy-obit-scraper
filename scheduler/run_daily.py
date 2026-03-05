"""
Daily cron entry point for the Legacy obituary scraper.

Loads markets.json, loops each market sequentially (no concurrency — polite),
scrapes today's obituaries, and writes results to MySQL.

Cron schedule: 0 6 * * * (6 AM CT daily)
"""

import json
import os
import sys
import traceback

# Add project root to path so imports work from cron
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.legacy_scraper import LegacyScraper
from scraper.db_writer import get_connection, upsert_obit, log_run
from utils.logger import get_logger

log = get_logger(__name__)

# Path to markets config relative to project root
MARKETS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config",
    "markets.json",
)


def load_markets():
    """
    Load market configurations from config/markets.json.

    Returns:
        List of market dicts.

    Raises:
        FileNotFoundError: If markets.json is missing.
        json.JSONDecodeError: If markets.json is malformed.
    """
    with open(MARKETS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def run():
    """
    Main daily scrape runner.

    Iterates all markets sequentially, scrapes each one, writes results to MySQL,
    and logs per-market summaries. Never runs markets concurrently.
    """
    log.info("[OK] Starting daily obituary scrape")

    markets = load_markets()
    log.info("[OK] Loaded %d markets from %s", len(markets), MARKETS_FILE)

    conn = get_connection()
    total_found = 0
    total_new = 0

    try:
        for market in markets:
            site_id = market.get("site_id") or "unknown"
            errors = None

            try:
                scraper = LegacyScraper(market, conn=conn)
                obits = scraper.scrape_today()

                found = len(obits)
                new = 0

                for obit in obits:
                    if upsert_obit(conn, obit, site_id):
                        new += 1

                total_found += found
                total_new += new

                log.info(
                    "[OK] %s: found=%d, new=%d",
                    site_id,
                    found,
                    new,
                )

            except Exception as exc:
                errors = f"{type(exc).__name__}: {exc}"
                log.error("[ERR] %s failed: %s", site_id, errors)
                log.error(traceback.format_exc())
                found = 0
                new = 0

            # Log every run, success or failure
            log_run(conn, site_id, found, new, errors)

    finally:
        conn.close()

    log.info(
        "[OK] Daily scrape complete: %d markets, %d found, %d new",
        len(markets),
        total_found,
        total_new,
    )


if __name__ == "__main__":
    run()
