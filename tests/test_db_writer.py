"""Tests for scraper.db_writer — database operations.

Uses unittest.mock to avoid requiring a live MySQL connection.
Tests the SQL generation and parameter handling logic.
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from scraper.db_writer import upsert_obit, log_run, url_exists


@pytest.fixture
def mock_conn():
    """Create a mock MySQL connection with a mock cursor."""
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    return conn


class TestUrlExists:
    """Tests for url_exists() — duplicate check."""

    def test_url_found(self, mock_conn):
        """Returns True when URL exists in DB."""
        mock_conn.cursor.return_value.fetchone.return_value = (1,)
        assert url_exists(mock_conn, "https://www.legacy.com/us/obituaries/name/test") is True

    def test_url_not_found(self, mock_conn):
        """Returns False when URL not in DB."""
        mock_conn.cursor.return_value.fetchone.return_value = None
        assert url_exists(mock_conn, "https://www.legacy.com/us/obituaries/name/new") is False

    def test_cursor_closed(self, mock_conn):
        """Cursor is always closed after check."""
        mock_conn.cursor.return_value.fetchone.return_value = None
        url_exists(mock_conn, "https://example.com")
        mock_conn.cursor.return_value.close.assert_called_once()


class TestUpsertObit:
    """Tests for upsert_obit() — INSERT IGNORE logic."""

    def test_new_record_returns_true(self, mock_conn):
        """Returns True when a new row is inserted (rowcount == 1)."""
        mock_conn.cursor.return_value.rowcount = 1
        obit = {
            "url": "https://www.legacy.com/us/obituaries/name/john-smith",
            "deceased_name": "John Smith",
            "first_name": "John",
            "middle_name": "",
            "last_name": "Smith",
            "name_suffix": "",
            "published_date": "2026-03-01",
            "death_date": "2026-02-28",
            "funeral_home": "Springfield Memorial",
            "obit_text": "John Smith passed away.",
        }
        result = upsert_obit(mock_conn, obit, "tx-brown")
        assert result is True
        mock_conn.commit.assert_called_once()

    def test_duplicate_returns_false(self, mock_conn):
        """Returns False when INSERT IGNORE skips duplicate (rowcount == 0)."""
        mock_conn.cursor.return_value.rowcount = 0
        obit = {
            "url": "https://www.legacy.com/us/obituaries/name/existing",
            "deceased_name": "Existing Person",
            "first_name": "Existing",
            "middle_name": "",
            "last_name": "Person",
            "name_suffix": "",
            "published_date": None,
            "death_date": None,
            "funeral_home": None,
            "obit_text": "",
        }
        result = upsert_obit(mock_conn, obit, "oh-franklin")
        assert result is False

    def test_none_fields_handled(self, mock_conn):
        """Missing dict keys default to empty string via .get() or ''."""
        mock_conn.cursor.return_value.rowcount = 1
        obit = {"url": "https://example.com/obit"}  # Minimal dict
        result = upsert_obit(mock_conn, obit, "test")
        assert result is True
        # Verify execute was called with params containing empty defaults
        call_args = mock_conn.cursor.return_value.execute.call_args
        params = call_args[0][1]
        assert params["deceased_name"] == ""
        assert params["first_name"] == ""

    def test_cursor_closed_on_success(self, mock_conn):
        """Cursor is closed after successful insert."""
        mock_conn.cursor.return_value.rowcount = 1
        obit = {"url": "https://example.com/obit"}
        upsert_obit(mock_conn, obit, "test")
        mock_conn.cursor.return_value.close.assert_called_once()


class TestLogRun:
    """Tests for log_run() — scrape run logging."""

    def test_log_success(self, mock_conn):
        """Logs a successful run with counts."""
        log_run(mock_conn, "tx-brown", found=5, new=3)
        mock_conn.cursor.return_value.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    def test_log_with_errors(self, mock_conn):
        """Logs a run with error message."""
        log_run(mock_conn, "oh-franklin", found=0, new=0, errors="HTTP 403")
        call_args = mock_conn.cursor.return_value.execute.call_args
        params = call_args[0][1]
        assert params["errors"] == "HTTP 403"
        assert params["obits_found"] == 0

    def test_log_cursor_closed(self, mock_conn):
        """Cursor is closed after logging."""
        log_run(mock_conn, "test", found=0, new=0)
        mock_conn.cursor.return_value.close.assert_called_once()
