"""
MySQL database writer for the Legacy obituary scraper.

Handles upsert of obituary records and scrape run logging.
Uses INSERT IGNORE on the legacy_url unique key for deduplication.
"""

import os
from datetime import date, datetime, timezone

import mysql.connector
from dotenv import load_dotenv

from utils.logger import get_logger

log = get_logger(__name__)

load_dotenv()

# SQL for inserting a new obituary (INSERT IGNORE deduplicates on legacy_url)
INSERT_OBIT_SQL = """
    INSERT IGNORE INTO obituaries
        (site_id, legacy_url, deceased_name, first_name, middle_name,
         last_name, name_suffix, published_date, death_date,
         funeral_home, obit_text, scraped_at)
    VALUES
        (%(site_id)s, %(legacy_url)s, %(deceased_name)s, %(first_name)s,
         %(middle_name)s, %(last_name)s, %(name_suffix)s,
         %(published_date)s, %(death_date)s, %(funeral_home)s,
         %(obit_text)s, %(scraped_at)s)
"""

# SQL for logging a scrape run
INSERT_LOG_SQL = """
    INSERT INTO scrape_log (site_id, run_date, obits_found, obits_new, errors)
    VALUES (%(site_id)s, %(run_date)s, %(obits_found)s, %(obits_new)s, %(errors)s)
"""

# SQL to check if a URL already exists (for pre-filtering before page fetch)
CHECK_URL_SQL = "SELECT 1 FROM obituaries WHERE legacy_url = %s LIMIT 1"


def get_connection():
    """
    Create and return a MySQL connection using .env credentials.

    Returns:
        mysql.connector.connection.MySQLConnection

    Raises:
        mysql.connector.Error: If connection fails.
    """
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", ""),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", ""),
        charset="utf8mb4",
    )


def url_exists(conn, url):
    """
    Check if an obituary URL already exists in the database.

    Used to skip fetching individual obit pages we already have.

    Args:
        conn: MySQL connection.
        url: Legacy.com obituary URL string.

    Returns:
        True if URL exists, False otherwise.
    """
    cursor = conn.cursor()
    try:
        cursor.execute(CHECK_URL_SQL, (url,))
        return cursor.fetchone() is not None
    finally:
        cursor.close()


def upsert_obit(conn, obit_dict, site_id):
    """
    Insert an obituary record, ignoring duplicates on legacy_url.

    Args:
        conn: MySQL connection.
        obit_dict: Dict with obituary data from obit_parser.
        site_id: Market site_id string.

    Returns:
        True if a new row was inserted, False if duplicate (already existed).
    """
    cursor = conn.cursor()
    try:
        params = {
            "site_id": site_id,
            "legacy_url": obit_dict.get("url") or "",
            "deceased_name": obit_dict.get("deceased_name") or "",
            "first_name": obit_dict.get("first_name") or "",
            "middle_name": obit_dict.get("middle_name") or "",
            "last_name": obit_dict.get("last_name") or "",
            "name_suffix": obit_dict.get("name_suffix") or "",
            "published_date": obit_dict.get("published_date"),
            "death_date": obit_dict.get("death_date"),
            "funeral_home": obit_dict.get("funeral_home"),
            "obit_text": obit_dict.get("obit_text") or "",
            "scraped_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        }
        cursor.execute(INSERT_OBIT_SQL, params)
        conn.commit()

        # rowcount == 1 means new row inserted; 0 means duplicate ignored
        return cursor.rowcount == 1

    except mysql.connector.Error as exc:
        log.error("[ERR] Failed to upsert obit %s: %s", obit_dict.get("url"), exc)
        conn.rollback()
        return False
    finally:
        cursor.close()


def log_run(conn, site_id, found, new, errors=None):
    """
    Write a scrape run summary to the scrape_log table.

    Args:
        conn: MySQL connection.
        site_id: Market site_id string.
        found: Total obituaries found on the listing page.
        new: Number of new obituaries inserted.
        errors: Error message string, or None if no errors.
    """
    cursor = conn.cursor()
    try:
        params = {
            "site_id": site_id,
            "run_date": date.today().isoformat(),
            "obits_found": found,
            "obits_new": new,
            "errors": errors,
        }
        cursor.execute(INSERT_LOG_SQL, params)
        conn.commit()
    except mysql.connector.Error as exc:
        log.error("[ERR] Failed to log run for %s: %s", site_id, exc)
        conn.rollback()
    finally:
        cursor.close()
