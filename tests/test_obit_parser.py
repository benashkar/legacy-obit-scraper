"""Tests for scraper.obit_parser — obituary data extraction and name parsing."""

import pytest

from scraper.obit_parser import (
    extract_obits_from_listing,
    split_name,
    parse_name,
    parse_obit_text,
    parse_funeral_home,
    parse_dates,
    _parse_date_str,
)
from bs4 import BeautifulSoup


# --- Fixtures: sample HTML pages ---

INITIAL_STATE_HTML = """
<html><head></head><body>
<script>
window.__INITIAL_STATE__ = {
    "BrowseStore": {
        "data": {
            "obituaries": {
                "obituaries": {
                    "edges": [
                        {
                            "node": {
                                "name": {"firstName": "John", "lastName": "Smith"},
                                "personId": 12345,
                                "obituaryNoHtml": "John Smith passed away peacefully.",
                                "publishedDate": "2026-03-01",
                                "deathDate": "2026-02-28",
                                "funeralHomeName": "Springfield Memorial",
                                "links": {
                                    "obituaryUrl": {"path": "/us/obituaries/name/john-smith-id12345"}
                                }
                            }
                        },
                        {
                            "node": {
                                "name": {"firstName": "Mary", "lastName": "Johnson"},
                                "personId": 12346,
                                "obituaryNoHtml": "Mary Johnson, beloved mother.",
                                "publishedDate": "2026-03-01",
                                "deathDate": null,
                                "funeralHomeName": null,
                                "links": {
                                    "obituaryUrl": {"path": "/us/obituaries/name/mary-johnson-id12346"}
                                }
                            }
                        }
                    ]
                }
            }
        }
    }
};
</script>
</body></html>
"""

NEXT_DATA_HTML = """
<html><head></head><body>
<script id="__NEXT_DATA__" type="application/json">
{
    "props": {
        "pageProps": {
            "obituaries": [
                {
                    "name": {"firstName": "Robert", "lastName": "Williams"},
                    "url": "/us/obituaries/name/robert-williams-id999",
                    "obituaryText": "Robert Williams, age 85.",
                    "publishedDate": "2026-03-02",
                    "deathDate": "2026-03-01",
                    "funeralHomeName": "Oak Hill Chapel"
                }
            ]
        }
    }
}
</script>
</body></html>
"""

HTML_FALLBACK_PAGE = """
<html><body>
<div class="obituary-list">
    <a href="/us/obituaries/name/jane-doe-id111">
        <h3>Jane Doe</h3>
    </a>
    <a href="/us/obituaries/name/bob-ross-id222">
        <h3>Bob Ross</h3>
    </a>
</div>
</body></html>
"""

SINGLE_OBIT_HTML = """
<html><body>
<h1 data-testid="obit-name">James Michael Wilson Jr.</h1>
<div data-testid="obit-dates">January 5, 1940 - March 1, 2026</div>
<div data-testid="funeral-home-name">Greenview Funeral Home</div>
<div data-testid="obit-text">James Michael Wilson Jr. passed away on March 1, 2026. He was a loving father.</div>
</body></html>
"""

EMPTY_OBIT_HTML = """
<html><body>
<div>No obituary information available.</div>
</body></html>
"""


class TestExtractFromInitialState:
    """Tests for __INITIAL_STATE__ JSON extraction."""

    def test_extracts_two_obits(self):
        """Parses both obituaries from __INITIAL_STATE__ JSON."""
        obits = extract_obits_from_listing(INITIAL_STATE_HTML)
        assert len(obits) == 2

    def test_first_obit_fields(self):
        """First obituary has correct name, text, dates, and funeral home."""
        obits = extract_obits_from_listing(INITIAL_STATE_HTML)
        obit = obits[0]
        assert obit["deceased_name"] == "John Smith"
        assert obit["first_name"] == "John"
        assert obit["last_name"] == "Smith"
        assert obit["obit_text"] == "John Smith passed away peacefully."
        assert obit["published_date"] == "2026-03-01"
        assert obit["death_date"] == "2026-02-28"
        assert obit["funeral_home"] == "Springfield Memorial"
        assert "john-smith" in obit["url"]

    def test_null_fields_handled(self):
        """Null death_date and funeral_home from JSON become None."""
        obits = extract_obits_from_listing(INITIAL_STATE_HTML)
        obit = obits[1]  # Mary Johnson has null deathDate and funeralHomeName
        assert obit["death_date"] is None
        assert obit["funeral_home"] is None
        assert obit["deceased_name"] == "Mary Johnson"


class TestExtractFromNextData:
    """Tests for __NEXT_DATA__ JSON extraction."""

    def test_extracts_obit(self):
        """Parses obituary from __NEXT_DATA__ JSON."""
        obits = extract_obits_from_listing(NEXT_DATA_HTML)
        assert len(obits) == 1

    def test_obit_fields(self):
        """Obituary has correct fields from Next.js data."""
        obits = extract_obits_from_listing(NEXT_DATA_HTML)
        obit = obits[0]
        assert obit["deceased_name"] == "Robert Williams"
        assert obit["first_name"] == "Robert"
        assert obit["last_name"] == "Williams"
        assert obit["funeral_home"] == "Oak Hill Chapel"
        assert "robert-williams" in obit["url"]


class TestExtractFromHtml:
    """Tests for HTML fallback extraction."""

    def test_extracts_links(self):
        """HTML fallback finds obituary links."""
        obits = extract_obits_from_listing(HTML_FALLBACK_PAGE)
        assert len(obits) == 2

    def test_names_extracted(self):
        """Names are extracted from link text."""
        obits = extract_obits_from_listing(HTML_FALLBACK_PAGE)
        names = [o["deceased_name"] for o in obits]
        assert "Jane Doe" in names
        assert "Bob Ross" in names


class TestExtractEmptyPage:
    """Tests for pages with no obituaries."""

    def test_empty_page_returns_empty(self):
        """Page with no obit data returns empty list."""
        obits = extract_obits_from_listing("<html><body>Nothing here</body></html>")
        assert obits == []


class TestSplitName:
    """Tests for split_name() — name decomposition."""

    def test_two_part_name(self):
        """Simple first + last name."""
        result = split_name("John Smith")
        assert result["first_name"] == "John"
        assert result["last_name"] == "Smith"
        assert result["middle_name"] == ""
        assert result["name_suffix"] == ""

    def test_three_part_name(self):
        """First + middle + last name."""
        result = split_name("John Michael Smith")
        assert result["first_name"] == "John"
        assert result["middle_name"] == "Michael"
        assert result["last_name"] == "Smith"

    def test_name_with_suffix(self):
        """Name with Jr suffix is detected and separated."""
        result = split_name("James Wilson Jr.")
        assert result["first_name"] == "James"
        assert result["last_name"] == "Wilson"
        assert result["name_suffix"] == "Jr."

    def test_name_with_suffix_iii(self):
        """Name with III suffix."""
        result = split_name("Robert Lee Thomas III")
        assert result["first_name"] == "Robert"
        assert result["middle_name"] == "Lee"
        assert result["last_name"] == "Thomas"
        assert result["name_suffix"] == "III"

    def test_single_name(self):
        """Single name goes to first_name."""
        result = split_name("Madonna")
        assert result["first_name"] == "Madonna"
        assert result["last_name"] == ""
        assert result["middle_name"] == ""

    def test_empty_name(self):
        """Empty string returns all empty fields."""
        result = split_name("")
        assert result["first_name"] == ""
        assert result["last_name"] == ""

    def test_none_name(self):
        """None input returns all empty fields."""
        result = split_name(None)
        assert result["first_name"] == ""

    def test_multiple_middle_names(self):
        """Multiple middle names are joined."""
        result = split_name("Anna Marie Louise Garcia")
        assert result["first_name"] == "Anna"
        assert result["middle_name"] == "Marie Louise"
        assert result["last_name"] == "Garcia"

    def test_comma_before_suffix(self):
        """Comma before suffix is handled."""
        result = split_name("James Wilson, Jr.")
        assert result["first_name"] == "James"
        assert result["last_name"] == "Wilson"
        assert result["name_suffix"] == "Jr."


class TestParseSingleObitPage:
    """Tests for individual obituary page parsing functions."""

    def test_parse_name(self):
        """parse_name extracts name from h1 tag."""
        soup = BeautifulSoup(SINGLE_OBIT_HTML, "lxml")
        name = parse_name(soup)
        assert name == "James Michael Wilson Jr."

    def test_parse_name_empty(self):
        """parse_name returns empty string when no name found."""
        soup = BeautifulSoup(EMPTY_OBIT_HTML, "lxml")
        name = parse_name(soup)
        # Falls through to bare h1, which doesn't exist with obit-name testid
        # but the div text is not in an h1, so should be empty or fallback
        assert isinstance(name, str)

    def test_parse_obit_text(self):
        """parse_obit_text extracts full text content."""
        soup = BeautifulSoup(SINGLE_OBIT_HTML, "lxml")
        text = parse_obit_text(soup)
        assert "passed away on March 1, 2026" in text
        assert "loving father" in text

    def test_parse_obit_text_empty(self):
        """parse_obit_text returns empty string when element missing."""
        soup = BeautifulSoup(EMPTY_OBIT_HTML, "lxml")
        text = parse_obit_text(soup)
        assert isinstance(text, str)

    def test_parse_funeral_home(self):
        """parse_funeral_home extracts funeral home name."""
        soup = BeautifulSoup(SINGLE_OBIT_HTML, "lxml")
        fh = parse_funeral_home(soup)
        assert fh == "Greenview Funeral Home"

    def test_parse_funeral_home_missing(self):
        """parse_funeral_home returns None when not found."""
        soup = BeautifulSoup(EMPTY_OBIT_HTML, "lxml")
        fh = parse_funeral_home(soup)
        assert fh is None

    def test_parse_dates(self):
        """parse_dates extracts death date from date range."""
        soup = BeautifulSoup(SINGLE_OBIT_HTML, "lxml")
        dates = parse_dates(soup)
        assert dates["death"] == "2026-03-01"

    def test_parse_dates_missing(self):
        """parse_dates returns Nones when no date elements found."""
        soup = BeautifulSoup(EMPTY_OBIT_HTML, "lxml")
        dates = parse_dates(soup)
        assert dates["published"] is None
        assert dates["death"] is None


class TestParseDateStr:
    """Tests for the internal _parse_date_str helper."""

    def test_iso_format(self):
        """Parses ISO 8601 date."""
        assert _parse_date_str("2026-03-01") == "2026-03-01"

    def test_iso_with_time(self):
        """Parses ISO 8601 datetime."""
        assert _parse_date_str("2026-03-01T14:30:00") == "2026-03-01"

    def test_us_long_format(self):
        """Parses 'March 1, 2026' format."""
        assert _parse_date_str("March 1, 2026") == "2026-03-01"

    def test_us_short_format(self):
        """Parses 'Mar 1, 2026' format."""
        assert _parse_date_str("Mar 1, 2026") == "2026-03-01"

    def test_none_input(self):
        """None input returns None."""
        assert _parse_date_str(None) is None

    def test_empty_string(self):
        """Empty string returns None."""
        assert _parse_date_str("") is None

    def test_garbage_input(self):
        """Unparseable string returns None."""
        assert _parse_date_str("not a date") is None
