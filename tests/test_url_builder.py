"""Tests for scraper.url_builder — URL construction from market configs."""

import pytest

from scraper.url_builder import build_listing_url, build_all_urls


class TestBuildListingUrl:
    """Tests for build_listing_url()."""

    def test_county_url(self):
        """County market produces correct Legacy.com URL."""
        market = {"site_id": "tx-brown", "state": "texas", "legacy_slug": "brown-county", "type": "county"}
        url = build_listing_url(market)
        assert url == "https://www.legacy.com/us/obituaries/local/texas/brown-county"

    def test_city_url(self):
        """City market produces correct Legacy.com URL."""
        market = {"site_id": "oh-hilliard", "state": "ohio", "legacy_slug": "hilliard", "type": "city"}
        url = build_listing_url(market)
        assert url == "https://www.legacy.com/us/obituaries/local/ohio/hilliard"

    def test_state_normalization(self):
        """State name is lowercased in URL."""
        market = {"site_id": "ma-grafton", "state": "Massachusetts", "legacy_slug": "grafton", "type": "city"}
        url = build_listing_url(market)
        assert url == "https://www.legacy.com/us/obituaries/local/massachusetts/grafton"

    def test_whitespace_stripped(self):
        """Leading/trailing whitespace in state and slug is stripped."""
        market = {"site_id": "test", "state": "  ohio  ", "legacy_slug": "  hilliard  ", "type": "city"}
        url = build_listing_url(market)
        assert url == "https://www.legacy.com/us/obituaries/local/ohio/hilliard"

    def test_missing_state_raises(self):
        """Missing state key raises ValueError."""
        market = {"site_id": "test", "legacy_slug": "hilliard"}
        with pytest.raises(ValueError):
            build_listing_url(market)

    def test_missing_slug_raises(self):
        """Missing legacy_slug key raises ValueError."""
        market = {"site_id": "test", "state": "ohio"}
        with pytest.raises(ValueError):
            build_listing_url(market)

    def test_empty_state_raises(self):
        """Empty state string raises ValueError."""
        market = {"site_id": "test", "state": "", "legacy_slug": "hilliard"}
        with pytest.raises(ValueError):
            build_listing_url(market)


class TestBuildAllUrls:
    """Tests for build_all_urls()."""

    def test_multiple_markets(self):
        """Returns correct (market, url) tuples for multiple markets."""
        markets = [
            {"site_id": "tx-brown", "state": "texas", "legacy_slug": "brown-county", "type": "county"},
            {"site_id": "oh-hilliard", "state": "ohio", "legacy_slug": "hilliard", "type": "city"},
        ]
        results = build_all_urls(markets)
        assert len(results) == 2
        assert results[0][0]["site_id"] == "tx-brown"
        assert "texas/brown-county" in results[0][1]
        assert results[1][0]["site_id"] == "oh-hilliard"
        assert "ohio/hilliard" in results[1][1]

    def test_empty_list(self):
        """Empty market list returns empty results."""
        assert build_all_urls([]) == []
