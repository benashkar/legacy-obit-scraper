"""One-time script to backfill birth_date and death_date for existing obituaries.

Reads obit_text from rows missing one or both dates and runs the date
extractor to populate them.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.date_extractor import extract_dates_from_text
from scraper.db_writer import get_connection
from utils.logger import get_logger

log = get_logger(__name__)

SELECT_SQL = """
    SELECT id, obit_text, birth_date, death_date
    FROM obituaries
    WHERE obit_text IS NOT NULL
      AND obit_text != ''
      AND (birth_date IS NULL OR death_date IS NULL)
"""

BATCH_SIZE = 100


def backfill():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    update_cursor = conn.cursor()

    total = 0
    birth_updated = 0
    death_updated = 0

    try:
        cursor.execute(SELECT_SQL)
        rows = cursor.fetchall()
        log.info("[OK] Found %d rows to process", len(rows))

        for i, row in enumerate(rows, start=1):
            dates = extract_dates_from_text(row["obit_text"])

            sets = []
            vals = []

            # Only update birth_date if the row is missing it and we extracted one
            if row["birth_date"] is None and dates["birth_date"] is not None:
                sets.append("birth_date = %s")
                vals.append(dates["birth_date"])
                birth_updated += 1

            # Only update death_date if the row is missing it and we extracted one
            if row["death_date"] is None and dates["death_date"] is not None:
                sets.append("death_date = %s")
                vals.append(dates["death_date"])
                death_updated += 1

            if sets:
                sql = f"UPDATE obituaries SET {', '.join(sets)} WHERE id = %s"
                vals.append(row["id"])
                update_cursor.execute(sql, vals)

            total += 1

            if i % BATCH_SIZE == 0:
                conn.commit()
                log.info("[--] Committed batch at row %d", i)

        # Final commit for remaining rows
        conn.commit()
        log.info("[OK] Final commit done")

    except Exception:
        conn.rollback()
        log.exception("[ERR] Backfill failed, rolled back")
        raise
    finally:
        cursor.close()
        update_cursor.close()
        conn.close()

    log.info("[OK] Backfill complete")
    log.info("[OK]   Rows processed:      %d", total)
    log.info("[OK]   birth_dates updated:  %d", birth_updated)
    log.info("[OK]   death_dates updated:  %d", death_updated)


if __name__ == "__main__":
    backfill()
