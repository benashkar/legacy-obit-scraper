"""Tests for the Flask dashboard — health check, index, and filters."""

from unittest.mock import patch, MagicMock

import pytest

from dashboard.app import create_app


class TestConfig:
    TESTING = True
    DB_HOST = "localhost"
    DB_PORT = 3306
    DB_USER = "test"
    DB_PASSWORD = "test"
    DB_NAME = "test"
    SECRET_KEY = "test-secret"


@pytest.fixture
def app():
    return create_app(TestConfig)


@pytest.fixture
def client(app):
    return app.test_client()


class TestHealthCheck:
    def test_health_returns_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "ok"


class TestIndex:
    @patch("dashboard.routes.main.get_db")
    def test_index_renders(self, mock_get_db, client):
        """Index page renders with mocked DB."""
        mock_conn = MagicMock()
        mock_get_db.return_value = mock_conn

        # First cursor call: obit query
        obit_cursor = MagicMock()
        obit_cursor.fetchall.return_value = []

        # Second cursor call: dropdown query
        dropdown_cursor = MagicMock()
        dropdown_cursor.fetchone.return_value = {
            "funeral_homes": "",
            "cities": "",
            "counties": "",
            "states": "",
        }

        mock_conn.cursor.side_effect = [obit_cursor, dropdown_cursor]

        resp = client.get("/")
        assert resp.status_code == 200
        assert b"CR Obituaries" in resp.data

    @patch("dashboard.routes.main.get_db")
    def test_index_with_filters(self, mock_get_db, client):
        """Filter params are applied to SQL query."""
        mock_conn = MagicMock()
        mock_get_db.return_value = mock_conn

        obit_cursor = MagicMock()
        obit_cursor.fetchall.return_value = []

        dropdown_cursor = MagicMock()
        dropdown_cursor.fetchone.return_value = {
            "funeral_homes": "",
            "cities": "",
            "counties": "",
            "states": "",
        }

        mock_conn.cursor.side_effect = [obit_cursor, dropdown_cursor]

        resp = client.get("/?state=TX&city=Brownwood")
        assert resp.status_code == 200

        # Verify the SQL had WHERE clauses with params
        call_args = obit_cursor.execute.call_args
        sql = call_args[0][0]
        params = call_args[0][1]
        assert "duplicate_of IS NULL" in sql
        assert "state = %s" in sql
        assert "city LIKE %s" in sql
        assert "TX" in params
        assert "%Brownwood%" in params

    @patch("dashboard.routes.main.get_db")
    def test_obits_displayed(self, mock_get_db, client):
        """Obituary rows appear in the rendered table."""
        mock_conn = MagicMock()
        mock_get_db.return_value = mock_conn

        obit_cursor = MagicMock()
        obit_cursor.fetchall.return_value = [
            {
                "deceased_name": "John Smith",
                "first_name": "John",
                "last_name": "Smith",
                "death_date": "2026-03-01",
                "published_date": "2026-03-02",
                "funeral_home": "Test FH",
                "city": "Columbus",
                "county": "Franklin",
                "state": "OH",
                "legacy_url": "https://www.legacy.com/us/obituaries/name/john-smith",
                "site_id": "oh-franklin",
            }
        ]

        dropdown_cursor = MagicMock()
        dropdown_cursor.fetchone.return_value = {
            "funeral_homes": "Test FH",
            "cities": "Columbus",
            "counties": "Franklin",
            "states": "OH",
        }

        mock_conn.cursor.side_effect = [obit_cursor, dropdown_cursor]

        resp = client.get("/")
        assert resp.status_code == 200
        assert b"John Smith" in resp.data
        assert b"Test FH" in resp.data
        assert b"Columbus" in resp.data
