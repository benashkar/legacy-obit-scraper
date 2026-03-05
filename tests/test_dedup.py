"""Tests for scraper.dedup — person-level deduplication."""

from unittest.mock import MagicMock, call

from scraper.dedup import run_dedup


class TestRunDedup:
    """Tests for run_dedup() — marking duplicate obituary rows."""

    def _make_conn(self, groups, group_rows_map):
        """Build a mock connection that returns dupe groups and their rows.

        Args:
            groups: List of (fn, ln, ct, st, cnt) tuples from FIND_DUPE_GROUPS_SQL.
            group_rows_map: Dict mapping (fn, ln, ct, st) to list of
                            (id, death_date, text_len, scraped_at) tuples.
        """
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value = cursor

        call_count = {"n": 0}
        results = [groups]
        for fn, ln, ct, st, _cnt in groups:
            results.append(group_rows_map[(fn, ln, ct, st)])

        def fake_execute(sql, params=None):
            pass

        def fake_fetchall():
            idx = call_count["n"]
            call_count["n"] += 1
            return results[idx]

        cursor.execute = fake_execute
        cursor.fetchall = fake_fetchall
        return conn, cursor

    def test_no_groups_returns_zero(self):
        """No duplicate groups means nothing to mark."""
        conn, cursor = self._make_conn([], {})
        result = run_dedup(conn)
        assert result == 0

    def test_marks_duplicates(self):
        """Two rows for same person → second row gets duplicate_of = first row's id."""
        groups = [("john", "smith", "columbus", "oh", 2)]
        group_rows = {
            ("john", "smith", "columbus", "oh"): [
                (10, "2026-03-01", 500, "2026-03-01 08:00:00"),  # primary (has death_date)
                (20, None, 200, "2026-03-02 08:00:00"),          # duplicate
            ],
        }
        conn, cursor = self._make_conn(groups, group_rows)

        # Track execute calls
        execute_calls = []
        def track_execute(sql, params=None):
            execute_calls.append((sql, params))

        cursor.execute = track_execute

        result = run_dedup(conn)
        assert result == 1

        # The UPDATE call should mark row 20 as duplicate of row 10
        update_calls = [(s, p) for s, p in execute_calls if p and len(p) == 2]
        assert len(update_calls) == 1
        assert update_calls[0][1] == (10, 20)

    def test_three_way_dupe(self):
        """Three rows for same person → 2 get marked, best one stays primary."""
        groups = [("gene", "adams", "seymour", "tx", 3)]
        group_rows = {
            ("gene", "adams", "seymour", "tx"): [
                (1, None, 800, "2026-03-01 08:00:00"),  # primary (longest text)
                (2, None, 300, "2026-03-01 09:00:00"),  # dupe
                (3, None, 200, "2026-03-02 08:00:00"),  # dupe
            ],
        }
        conn, cursor = self._make_conn(groups, group_rows)

        execute_calls = []
        def track_execute(sql, params=None):
            execute_calls.append((sql, params))

        cursor.execute = track_execute

        result = run_dedup(conn)
        assert result == 2

        update_calls = [(s, p) for s, p in execute_calls if p and len(p) == 2]
        assert len(update_calls) == 2
        # Both should reference primary_id=1
        assert update_calls[0][1] == (1, 2)
        assert update_calls[1][1] == (1, 3)

    def test_single_row_group_skipped(self):
        """Groups where fetchall returns <2 rows are safely skipped."""
        groups = [("solo", "person", "nowhere", "xx", 2)]
        group_rows = {
            ("solo", "person", "nowhere", "xx"): [
                (99, None, 100, "2026-03-01 08:00:00"),
            ],
        }
        conn, cursor = self._make_conn(groups, group_rows)
        cursor.execute = lambda sql, params=None: None

        result = run_dedup(conn)
        assert result == 0
