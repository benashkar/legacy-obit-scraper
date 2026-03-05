"""
Extract birth and death dates from obituary text.

Parses the first few sentences of obit text looking for common patterns:
  - Death: "passed away on March 3, 2026", "died February 16, 2026",
           "passed away peacefully on February 26th, 2026"
  - Birth: "born on February 4, 1952", "was born October 9, 1937",
           "Born on January 2, 1959"

Returns dates as YYYY-MM-DD strings or None.
"""

import re
from datetime import datetime

from utils.logger import get_logger

log = get_logger(__name__)

# Month pattern (full and abbreviated, with optional period)
_MONTH = (
    r"(?:January|February|March|April|May|June|July|August|September|"
    r"October|November|December|"
    r"Jan\.?|Feb\.?|Mar\.?|Apr\.?|Jun\.?|Jul\.?|Aug\.?|Sep(?:t)?\.?|"
    r"Oct\.?|Nov\.?|Dec\.?)"
)

# Date pattern: "March 3, 2026" or "February 26th, 2026" or "3/15/2026"
_DATE_MDY = (
    rf"({_MONTH})\s+(\d{{1,2}})(?:st|nd|rd|th)?,?\s+(\d{{4}})"
)
_DATE_NUMERIC = r"(\d{1,2})/(\d{1,2})/(\d{4})"

# Optional weekday prefix
_WEEKDAY = r"(?:(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+)?"

# Death patterns — order matters, most specific first
_DEATH_PATTERNS = [
    # "passed away [peacefully/quietly/suddenly/etc.] [on] [weekday,] DATE"
    rf"passed\s+away\s+(?:\w+\s+)*?(?:on\s+)?{_WEEKDAY}{_DATE_MDY}",
    # "passed [peacefully/quietly] on DATE" (no "away")
    rf"passed\s+(?:peacefully|quietly|suddenly|unexpectedly)\s+(?:on\s+)?{_WEEKDAY}{_DATE_MDY}",
    # "passed on [to ...] [on] DATE"
    rf"passed\s+on\s+(?:to\s+\S+\s+\S+\s+\S+\s+)?(?:on\s+)?{_WEEKDAY}{_DATE_MDY}",
    # "passed from this life ... on DATE"
    rf"passed\s+from\s+.{{1,40}}?\s+(?:on\s+)?{_WEEKDAY}{_DATE_MDY}",
    # "went home to be with the Lord on DATE" / "went to be with ... on DATE"
    rf"went\s+(?:home\s+)?to\s+be\s+with\s+.{{1,40}}?\s+(?:on\s+)?{_WEEKDAY}{_DATE_MDY}",
    # "entered eternal rest on DATE" / "entered into rest on DATE"
    rf"entered\s+(?:eternal\s+|into\s+)?rest\s+(?:on\s+)?{_WEEKDAY}{_DATE_MDY}",
    # "died [on] [weekday,] DATE"
    rf"died\s+(?:on\s+)?{_WEEKDAY}{_DATE_MDY}",
    # "death on DATE" / "death DATE"
    rf"death\s+(?:on\s+)?{_DATE_MDY}",
    # standalone date range: "Aug 17, 1939 - Feb 24, 2026" or "(1933 - March 1, 2026)"
    rf"[-\u2013\u2014]\s*{_DATE_MDY}",
    # numeric: "passed away 3/3/2026"
    rf"passed\s+away\s+(?:\w+\s+)*?{_DATE_NUMERIC}",
    rf"died\s+(?:on\s+)?{_DATE_NUMERIC}",
]

# Birth patterns
_BIRTH_PATTERNS = [
    # "born [on] DATE" / "was born [on/in] DATE" / "born to ... on DATE"
    rf"[Bb]orn\s+(?:to\s+.{{1,80}}?\s+(?:on\s+))?{_DATE_MDY}",
    rf"[Bb]orn\s+(?:on\s+|in\s+)?{_DATE_MDY}",
    # numeric: "born 2/4/1952"
    rf"[Bb]orn\s+(?:on\s+)?{_DATE_NUMERIC}",
]

# Compile all patterns (case-insensitive)
_DEATH_RE = [re.compile(p, re.IGNORECASE) for p in _DEATH_PATTERNS]
_BIRTH_RE = [re.compile(p, re.IGNORECASE) for p in _BIRTH_PATTERNS]

# Month name to number mapping
_MONTH_MAP = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}


def _month_to_num(month_str):
    """Convert month name/abbreviation to number."""
    clean = month_str.rstrip(".").lower()
    return _MONTH_MAP.get(clean)


def _to_date_str(month_str, day_str, year_str):
    """Convert parsed components to YYYY-MM-DD string."""
    try:
        # Handle numeric month (from M/D/YYYY pattern)
        if month_str.isdigit():
            month = int(month_str)
        else:
            month = _month_to_num(month_str)
            if not month:
                return None

        day = int(day_str)
        year = int(year_str)

        # Validate the date is real
        dt = datetime(year, month, day)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def extract_dates_from_text(obit_text):
    """
    Extract birth and death dates from obituary text.

    Searches the text for common death and birth date patterns.
    Returns the first match found for each.

    Args:
        obit_text: Full obituary text string.

    Returns:
        Dict with keys 'death_date' and 'birth_date', each YYYY-MM-DD or None.
    """
    result = {"death_date": None, "birth_date": None}

    if not obit_text:
        return result

    # Search for death date
    for pattern in _DEATH_RE:
        match = pattern.search(obit_text)
        if match:
            groups = match.groups()
            date_str = _to_date_str(groups[0], groups[1], groups[2])
            if date_str:
                result["death_date"] = date_str
                break

    # Search for birth date
    for pattern in _BIRTH_RE:
        match = pattern.search(obit_text)
        if match:
            groups = match.groups()
            date_str = _to_date_str(groups[0], groups[1], groups[2])
            if date_str:
                result["birth_date"] = date_str
                break

    return result
