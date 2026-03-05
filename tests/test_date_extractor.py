"""Tests for scraper.date_extractor — birth and death date extraction from obit text."""

import pytest

from scraper.date_extractor import extract_dates_from_text


# ---------------------------------------------------------------------------
# Death date patterns
# ---------------------------------------------------------------------------


class TestDeathDatePatterns:
    """Individual death-date pattern recognition."""

    def test_passed_away_peacefully_on(self):
        text = "Joe Blair passed away peacefully on March 3, 2026 at his home."
        result = extract_dates_from_text(text)
        assert result["death_date"] == "2026-03-03"

    def test_passed_away_on(self):
        text = "Gregory Bute passed away on February 26, 2026."
        result = extract_dates_from_text(text)
        assert result["death_date"] == "2026-02-26"

    def test_passed_away_ordinal_suffix(self):
        text = "She passed away peacefully on February 26th, 2026."
        result = extract_dates_from_text(text)
        assert result["death_date"] == "2026-02-26"

    def test_died_with_weekday(self):
        text = "He died Monday, February 16, 2026 at the age of 85."
        result = extract_dates_from_text(text)
        assert result["death_date"] == "2026-02-16"

    def test_passed_away_with_weekday_no_on(self):
        text = "Mary Smith passed away Tuesday, February 10, 2026."
        result = extract_dates_from_text(text)
        assert result["death_date"] == "2026-02-10"

    def test_passed_on_to_heavenly_reward(self):
        text = (
            "She passed on to her heavenly reward on Wednesday, "
            "February 11, 2026."
        )
        result = extract_dates_from_text(text)
        assert result["death_date"] == "2026-02-11"

    def test_went_home_to_be_with_the_lord(self):
        text = (
            "He went home to be with the Lord on Wednesday, "
            "February 25, 2026."
        )
        result = extract_dates_from_text(text)
        assert result["death_date"] == "2026-02-25"

    def test_entered_eternal_rest(self):
        text = "She entered eternal rest on Tuesday, February 25, 2026."
        result = extract_dates_from_text(text)
        assert result["death_date"] == "2026-02-25"

    def test_passed_peacefully_no_away(self):
        text = "He passed peacefully on February 23, 2026."
        result = extract_dates_from_text(text)
        assert result["death_date"] == "2026-02-23"

    def test_passed_from_this_life(self):
        text = "She passed from this life on February 24, 2026."
        result = extract_dates_from_text(text)
        assert result["death_date"] == "2026-02-24"

    def test_went_to_be_with_our_father(self):
        text = "He went to be with our Father on February 14, 2026."
        result = extract_dates_from_text(text)
        assert result["death_date"] == "2026-02-14"

    def test_date_range_dash(self):
        text = "Aug 17, 1939 - Feb 24, 2026"
        result = extract_dates_from_text(text)
        assert result["death_date"] == "2026-02-24"


# ---------------------------------------------------------------------------
# Birth date patterns
# ---------------------------------------------------------------------------


class TestBirthDatePatterns:
    """Individual birth-date pattern recognition."""

    def test_was_born_on(self):
        text = "He was born on February 4, 1952 in Springfield, IL."
        result = extract_dates_from_text(text)
        assert result["birth_date"] == "1952-02-04"

    def test_born_on_capitalized(self):
        text = "Born on January 2, 1959, she grew up in a large family."
        result = extract_dates_from_text(text)
        assert result["birth_date"] == "1959-01-02"

    def test_born_no_on(self):
        text = "She was born October 9, 1937 to John and Mary."
        result = extract_dates_from_text(text)
        assert result["birth_date"] == "1937-10-09"

    def test_was_born_no_on(self):
        text = "He was born February 18, 1948 in Chicago."
        result = extract_dates_from_text(text)
        assert result["birth_date"] == "1948-02-18"

    def test_born_on_capitalized_alt(self):
        text = "Born on July 1, 1976, she was the eldest daughter."
        result = extract_dates_from_text(text)
        assert result["birth_date"] == "1976-07-01"

    def test_born_to_parents_on_date(self):
        text = (
            "She was born to James Euell and Gracie Cosby Walls "
            "on April 18, 1931 in Memphis, TN."
        )
        result = extract_dates_from_text(text)
        assert result["birth_date"] == "1931-04-18"


# ---------------------------------------------------------------------------
# Combined / full-obit tests
# ---------------------------------------------------------------------------


class TestCombinedExtraction:
    """Tests with realistic full obituary text containing both dates."""

    def test_full_obit_both_dates(self):
        """Joe Blair example — both death and birth dates present."""
        text = (
            "Joe Edward 'Double' Blair, 74, of Springfield, IL passed away "
            "peacefully on March 3, 2026 at his home surrounded by family. "
            "He was born on February 4, 1952 in Springfield to James and "
            "Dorothy Blair. Joe was a loving father, grandfather, and friend "
            "to many. He retired from the railroad after 35 years of service."
        )
        result = extract_dates_from_text(text)
        assert result["death_date"] == "2026-03-03"
        assert result["birth_date"] == "1952-02-04"

    def test_full_obit_death_only(self):
        """Gregory Bute example — death date present, no birth date."""
        text = (
            "Gregory Allen Bute, age 63, passed away on February 26, 2026. "
            "Greg was a devoted husband and father. He enjoyed fishing, "
            "woodworking, and spending time with his grandchildren. "
            "A memorial service will be held Saturday at First Baptist Church."
        )
        result = extract_dates_from_text(text)
        assert result["death_date"] == "2026-02-26"
        assert result["birth_date"] is None

    def test_empty_string(self):
        result = extract_dates_from_text("")
        assert result["death_date"] is None
        assert result["birth_date"] is None

    def test_none_input(self):
        result = extract_dates_from_text(None)
        assert result["death_date"] is None
        assert result["birth_date"] is None

    def test_no_date_patterns(self):
        text = (
            "He was a beloved member of the community and will be greatly "
            "missed by all who knew him. Services pending."
        )
        result = extract_dates_from_text(text)
        assert result["death_date"] is None
        assert result["birth_date"] is None
