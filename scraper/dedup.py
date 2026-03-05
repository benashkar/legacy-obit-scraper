"""
Person-level deduplication for obituaries.

Legacy.com often publishes the same obituary under multiple URLs:
  - Generic: legacy.com/us/obituaries/name/john-smith-obituary?id=123
  - Affiliate: legacy.com/us/obituaries/brownwoodtx/name/john-smith-obituary?id=456

Adjacent county listings also surface the same person. Since we scrape
at the county level, the same obit can appear in multiple market scrapes.

Strategy:
  1. Group rows by (lower(first_name), lower(last_name), lower(city), lower(state))
  2. Within each group of >1 row, pick the "best" record as the primary
  3. Mark others with duplicate_of = primary.id
  4. Dashboard filters to duplicate_of IS NULL by default

"Best" record priority:
  - Has death_date (over NULL)
  - Longest obit_text (most complete)
  - Earliest scraped_at (first seen)
"""

from utils.logger import get_logger

log = get_logger(__name__)

# Find all groups of potential duplicates.
# Groups by normalized name + city + state where >1 row exists
# and at least one row is not yet marked as a duplicate.
FIND_DUPE_GROUPS_SQL = """
    SELECT LOWER(first_name) AS fn, LOWER(last_name) AS ln,
           LOWER(COALESCE(city, '')) AS ct, LOWER(COALESCE(state, '')) AS st,
           COUNT(*) AS cnt
    FROM obituaries
    WHERE first_name <> '' AND last_name <> ''
      AND duplicate_of IS NULL
    GROUP BY fn, ln, ct, st
    HAVING cnt > 1
"""

# Get all rows in a specific dupe group, ordered so the "best" record is first.
GET_GROUP_ROWS_SQL = """
    SELECT id, death_date, CHAR_LENGTH(COALESCE(obit_text, '')) AS text_len, scraped_at
    FROM obituaries
    WHERE LOWER(first_name) = %s AND LOWER(last_name) = %s
      AND LOWER(COALESCE(city, '')) = %s AND LOWER(COALESCE(state, '')) = %s
      AND duplicate_of IS NULL
    ORDER BY
        (death_date IS NOT NULL) DESC,
        CHAR_LENGTH(COALESCE(obit_text, '')) DESC,
        scraped_at ASC
"""

MARK_DUPLICATE_SQL = """
    UPDATE obituaries SET duplicate_of = %s WHERE id = %s
"""


def run_dedup(conn):
    """
    Scan for person-level duplicates and mark non-primary rows.

    Idempotent — only processes rows where duplicate_of IS NULL,
    so it's safe to run repeatedly.

    Args:
        conn: MySQL connection.

    Returns:
        Number of rows marked as duplicates.
    """
    cursor = conn.cursor()
    total_marked = 0

    try:
        cursor.execute(FIND_DUPE_GROUPS_SQL)
        groups = cursor.fetchall()
        log.info("[OK] Found %d duplicate groups to process", len(groups))

        for fn, ln, ct, st, cnt in groups:
            cursor.execute(GET_GROUP_ROWS_SQL, (fn, ln, ct, st))
            rows = cursor.fetchall()

            if len(rows) < 2:
                continue

            # First row is the primary (best record)
            primary_id = rows[0][0]

            # Mark all others as duplicates
            for row in rows[1:]:
                cursor.execute(MARK_DUPLICATE_SQL, (primary_id, row[0]))
                total_marked += 1

            conn.commit()

        log.info("[OK] Dedup complete: %d rows marked as duplicates", total_marked)

    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()

    return total_marked
