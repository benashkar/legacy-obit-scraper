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


# --- Fixtures: sample HTML pages mimicking real Legacy.com structure ---

# Current Legacy.com 2026 format: JSON in <script type="application/json"><!--{...}-->
EMBEDDED_JSON_HTML = """
<html><head></head><body>
<script type="application/json"><!--{
    "adMap": {"ads": []},
    "obituaryList": {
        "obituaries": [
            {
                "id": 211000142,
                "personId": 211000142,
                "name": {
                    "firstName": "Joe",
                    "lastName": "Blair",
                    "middleName": "Edward",
                    "nickName": "Double",
                    "maidenName": null,
                    "prefix": "",
                    "suffix": "",
                    "fullName": "Joe Edward \\"Double\\" Blair"
                },
                "funeralHome": {
                    "id": 19385,
                    "name": "Blaylock Funeral Home"
                },
                "obitSnippet": "Joe Edward Blair, 74, of Brownwood, passed away peacefully.",
                "links": {
                    "obituaryUrl": {
                        "href": "https://www.legacy.com/us/obituaries/name/joe-blair-obituary?id=60939051",
                        "path": "/us/obituaries/name/joe-blair-obituary?id=60939051"
                    }
                },
                "datePostedFrom": "2026-03-04T00:00:00",
                "publisherName": "Blaylock Funeral Home",
                "location": {
                    "city": {"fullName": "Brownwood"},
                    "state": {"code": "TX", "fullName": "Texas"}
                }
            },
            {
                "id": 211001408,
                "personId": 211001408,
                "name": {
                    "firstName": "Mary",
                    "lastName": "Johnson",
                    "middleName": "",
                    "nickName": null,
                    "maidenName": null,
                    "prefix": "",
                    "suffix": "Sr.",
                    "fullName": "Mary Johnson Sr."
                },
                "funeralHome": null,
                "obitSnippet": "Mary Johnson, beloved mother.",
                "links": {
                    "obituaryUrl": {
                        "href": "https://www.legacy.com/us/obituaries/name/mary-johnson-obituary?id=60940610",
                        "path": "/us/obituaries/name/mary-johnson-obituary?id=60940610"
                    }
                },
                "datePostedFrom": "2026-03-04T00:00:00",
                "publisherName": "Legacy Remembers",
                "location": null
            }
        ]
    },
    "notableObits": {"obituaries": []},
    "listView": {}
}--></script>
</body></html>
"""

# Older Legacy.com format: window.__INITIAL_STATE__
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


class TestExtractFromEmbeddedJson:
    """Tests for the current (2026) Legacy.com embedded JSON format."""

    def test_extracts_two_obits(self):
        """Parses both obituaries from embedded JSON."""
        obits = extract_obits_from_listing(EMBEDDED_JSON_HTML)
        assert len(obits) == 2

    def test_first_obit_structured_name(self):
        """First obit uses structured name fields from Legacy.com JSON."""
        obits = extract_obits_from_listing(EMBEDDED_JSON_HTML)
        obit = obits[0]
        assert obit["first_name"] == "Joe"
        assert obit["middle_name"] == "Edward"
        assert obit["last_name"] == "Blair"
        assert obit["deceased_name"] == 'Joe Edward "Double" Blair'

    def test_first_obit_funeral_home(self):
        """Funeral home extracted from funeralHome.name object."""
        obits = extract_obits_from_listing(EMBEDDED_JSON_HTML)
        assert obits[0]["funeral_home"] == "Blaylock Funeral Home"

    def test_first_obit_url(self):
        """URL comes from links.obituaryUrl.href."""
        obits = extract_obits_from_listing(EMBEDDED_JSON_HTML)
        assert "joe-blair-obituary" in obits[0]["url"]
        assert obits[0]["url"].startswith("https://")

    def test_first_obit_snippet(self):
        """Obit text is the snippet from listing."""
        obits = extract_obits_from_listing(EMBEDDED_JSON_HTML)
        assert "passed away peacefully" in obits[0]["obit_text"]

    def test_first_obit_date(self):
        """Published date parsed from ISO datePostedFrom."""
        obits = extract_obits_from_listing(EMBEDDED_JSON_HTML)
        assert obits[0]["published_date"] == "2026-03-04"

    def test_null_funeral_home_falls_back(self):
        """When funeralHome is null, falls back to publisherName."""
        obits = extract_obits_from_listing(EMBEDDED_JSON_HTML)
        assert obits[1]["funeral_home"] == "Legacy Remembers"

    def test_suffix_from_structured_data(self):
        """Suffix extracted from name.suffix field."""
        obits = extract_obits_from_listing(EMBEDDED_JSON_HTML)
        assert obits[1]["name_suffix"] == "Sr."

    def test_city_extracted(self):
        """City extracted from location.city.fullName."""
        obits = extract_obits_from_listing(EMBEDDED_JSON_HTML)
        assert obits[0]["city"] == "Brownwood"

    def test_state_extracted(self):
        """State extracted from location.state.code."""
        obits = extract_obits_from_listing(EMBEDDED_JSON_HTML)
        assert obits[0]["state"] == "TX"

    def test_null_location_defaults_empty(self):
        """When location is null, city/state default to empty string."""
        obits = extract_obits_from_listing(EMBEDDED_JSON_HTML)
        assert obits[1]["city"] == ""
        assert obits[1]["state"] == ""


class TestExtractFromInitialState:
    """Tests for older __INITIAL_STATE__ JSON extraction."""

    def test_extracts_obit(self):
        """Parses obituary from __INITIAL_STATE__ JSON."""
        obits = extract_obits_from_listing(INITIAL_STATE_HTML)
        assert len(obits) == 1

    def test_obit_fields(self):
        """Obituary has correct fields from older format."""
        obits = extract_obits_from_listing(INITIAL_STATE_HTML)
        obit = obits[0]
        assert obit["deceased_name"] == "John Smith"
        assert obit["first_name"] == "John"
        assert obit["last_name"] == "Smith"
        assert obit["funeral_home"] == "Springfield Memorial"
        assert obit["published_date"] == "2026-03-01"
        assert obit["death_date"] == "2026-02-28"


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

    def test_legacy_abbreviated_format(self):
        """Parses 'Mar. 4, 2026' format (Legacy.com style)."""
        assert _parse_date_str("Mar. 4, 2026") == "2026-03-04"

    def test_on_prefix_stripped(self):
        """Strips 'on ' prefix from Legacy.com date strings."""
        assert _parse_date_str("on Mar. 4, 2026") == "2026-03-04"

    def test_none_input(self):
        """None input returns None."""
        assert _parse_date_str(None) is None

    def test_empty_string(self):
        """Empty string returns None."""
        assert _parse_date_str("") is None

    def test_garbage_input(self):
        """Unparseable string returns None."""
        assert _parse_date_str("not a date") is None
