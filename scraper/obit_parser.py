"""
Stateless parsing functions for Legacy.com obituary data.

Two extraction strategies:
  1. JSON extraction from window.__INITIAL_STATE__ embedded in the page
     (preferred — structured data, matches ahplummer/LegacyObituaries pattern)
  2. BeautifulSoup HTML fallback for individual obituary pages

Name splitting follows data field standards:
  deceased_name (full), first_name, middle_name, last_name, name_suffix.
"""

import json
import re
from datetime import datetime

from bs4 import BeautifulSoup

from utils.logger import get_logger

log = get_logger(__name__)

# Regex to extract __INITIAL_STATE__ JSON from script tags
INITIAL_STATE_PATTERN = re.compile(
    r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\})\s*;",
    re.DOTALL,
)

# Regex to extract __NEXT_DATA__ JSON (modern Next.js Legacy.com pages)
NEXT_DATA_PATTERN = re.compile(
    r'<script\s+id="__NEXT_DATA__"[^>]*>\s*(\{.*?\})\s*</script>',
    re.DOTALL,
)

# Common name suffixes to detect and separate
NAME_SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v", "esq", "phd", "md", "dds"}


def extract_obits_from_listing(html):
    """
    Extract obituary entries from a Legacy.com listing page.

    Tries __INITIAL_STATE__ JSON first, then __NEXT_DATA__, then HTML fallback.

    Args:
        html: Raw HTML string of the listing page.

    Returns:
        List of dicts, each with keys:
            - url: Full obituary page URL
            - deceased_name: Full name string
            - first_name, middle_name, last_name, name_suffix: Parsed name parts
            - obit_text: Obituary text (may be truncated from listing)
            - published_date: Date string or None
            - death_date: Date string or None
            - funeral_home: Funeral home name or None
    """
    # Strategy 1: __INITIAL_STATE__ JSON
    obits = _extract_from_initial_state(html)
    if obits:
        return obits

    # Strategy 2: __NEXT_DATA__ JSON (Next.js)
    obits = _extract_from_next_data(html)
    if obits:
        return obits

    # Strategy 3: HTML fallback
    return _extract_from_html(html)


def _extract_from_initial_state(html):
    """
    Parse obituary data from the window.__INITIAL_STATE__ JSON blob.

    This matches the pattern from ahplummer/LegacyObituaries where Legacy.com
    embeds all listing data in a script tag as JSON.

    Args:
        html: Raw HTML string.

    Returns:
        List of obit dicts, or empty list if pattern not found.
    """
    match = INITIAL_STATE_PATTERN.search(html)
    if not match:
        return []

    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        log.warning("[WARN] Failed to parse __INITIAL_STATE__ JSON: %s", exc)
        return []

    # Navigate to the obituary edges — path from ahplummer reference
    edges = _deep_get(
        data, "BrowseStore", "data", "obituaries", "obituaries", "edges"
    )
    if not edges:
        # Try alternate path structures
        edges = _deep_get(data, "obituaries", "edges")

    if not edges:
        log.warning("[WARN] No obituary edges found in __INITIAL_STATE__")
        return []

    obits = []
    for edge in edges:
        node = edge.get("node") or {}
        name_obj = node.get("name") or {}

        first = name_obj.get("firstName") or ""
        last = name_obj.get("lastName") or ""
        full_name = f"{first} {last}".strip()

        # Parse name parts from the structured data
        parsed = split_name(full_name)

        # Build the obit URL
        links = node.get("links") or {}
        obit_url_obj = links.get("obituaryUrl") or {}
        path = obit_url_obj.get("path") or ""
        url = f"https://www.legacy.com{path}" if path else ""

        obits.append({
            "url": url,
            "deceased_name": full_name,
            "first_name": parsed["first_name"],
            "middle_name": parsed["middle_name"],
            "last_name": parsed["last_name"],
            "name_suffix": parsed["name_suffix"],
            "obit_text": node.get("obituaryNoHtml") or "",
            "published_date": _parse_date_str(node.get("publishedDate")),
            "death_date": _parse_date_str(node.get("deathDate")),
            "funeral_home": node.get("funeralHomeName"),
        })

    return obits


def _extract_from_next_data(html):
    """
    Parse obituary data from __NEXT_DATA__ JSON (Next.js server props).

    Modern Legacy.com pages may use Next.js and embed data differently.

    Args:
        html: Raw HTML string.

    Returns:
        List of obit dicts, or empty list if pattern not found.
    """
    match = NEXT_DATA_PATTERN.search(html)
    if not match:
        return []

    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        log.warning("[WARN] Failed to parse __NEXT_DATA__ JSON: %s", exc)
        return []

    # Navigate through Next.js page props
    page_props = _deep_get(data, "props", "pageProps")
    if not page_props:
        return []

    # Look for obituary list in various possible locations
    obit_list = (
        page_props.get("obituaries")
        or page_props.get("results")
        or _deep_get(page_props, "data", "obituaries")
        or []
    )

    obits = []
    for entry in obit_list:
        name_obj = entry.get("name") or {}
        first = name_obj.get("firstName") or entry.get("firstName") or ""
        last = name_obj.get("lastName") or entry.get("lastName") or ""

        if not first and not last:
            # Try a combined name field
            full_name = entry.get("name", "") if isinstance(entry.get("name"), str) else ""
        else:
            full_name = f"{first} {last}".strip()

        parsed = split_name(full_name)

        url = entry.get("url") or entry.get("obituaryUrl") or ""
        if url and not url.startswith("http"):
            url = f"https://www.legacy.com{url}"

        obits.append({
            "url": url,
            "deceased_name": full_name,
            "first_name": parsed["first_name"],
            "middle_name": parsed["middle_name"],
            "last_name": parsed["last_name"],
            "name_suffix": parsed["name_suffix"],
            "obit_text": entry.get("obituaryText") or entry.get("obituaryNoHtml") or "",
            "published_date": _parse_date_str(entry.get("publishedDate")),
            "death_date": _parse_date_str(entry.get("deathDate")),
            "funeral_home": entry.get("funeralHomeName") or entry.get("funeral_home"),
        })

    return obits


def _extract_from_html(html):
    """
    Fallback: extract obituary links from HTML using BeautifulSoup selectors.

    Less reliable than JSON extraction — selectors may change. Returns partial
    data (URL and name only); full details fetched from individual obit pages.

    Args:
        html: Raw HTML string.

    Returns:
        List of obit dicts with url and deceased_name populated.
    """
    soup = BeautifulSoup(html, "lxml")

    # Common Legacy.com listing card selectors (may need updating)
    # Try multiple selector patterns for robustness
    CARD_SELECTORS = [
        "a[data-testid='obituary-card']",
        "a.obit-card",
        "div.obituary-list a[href*='/obituary/']",
        "a[href*='/us/obituaries/name/']",
    ]

    links = []
    for selector in CARD_SELECTORS:
        links = soup.select(selector)
        if links:
            break

    if not links:
        log.warning("[WARN] HTML fallback found no obituary links")
        return []

    obits = []
    for link in links:
        href = link.get("href") or ""
        if not href:
            continue

        if not href.startswith("http"):
            href = f"https://www.legacy.com{href}"

        # Try to extract name from link text or child elements
        name_el = link.select_one("h3, h4, .obit-name, [data-testid='obit-name']")
        name_text = name_el.get_text(strip=True) if name_el else link.get_text(strip=True)
        parsed = split_name(name_text)

        obits.append({
            "url": href,
            "deceased_name": name_text,
            "first_name": parsed["first_name"],
            "middle_name": parsed["middle_name"],
            "last_name": parsed["last_name"],
            "name_suffix": parsed["name_suffix"],
            "obit_text": "",
            "published_date": None,
            "death_date": None,
            "funeral_home": None,
        })

    return obits


# --- Individual obituary page parsing ---

def parse_name(soup):
    """
    Extract the deceased person's name from an individual obituary page.

    Args:
        soup: BeautifulSoup object of the obituary page.

    Returns:
        Full name string, or empty string if not found.
    """
    # Try structured selectors first
    NAME_SELECTORS = [
        "h1[data-testid='obit-name']",
        "h1.obit-header-name",
        "h1.obituary-name",
        "h1",
    ]
    for selector in NAME_SELECTORS:
        el = soup.select_one(selector)
        if el:
            return el.get_text(strip=True)

    return ""


def parse_dates(soup):
    """
    Extract published and death dates from an individual obituary page.

    Args:
        soup: BeautifulSoup object of the obituary page.

    Returns:
        Dict with keys 'published' and 'death', each a date string or None.
    """
    result = {"published": None, "death": None}

    # Look for date spans/divs with common class patterns
    DATE_SELECTORS = [
        "[data-testid='obit-dates']",
        ".obit-dates",
        ".obituary-dates",
    ]

    for selector in DATE_SELECTORS:
        el = soup.select_one(selector)
        if el:
            text = el.get_text(strip=True)
            dates = _parse_date_range(text)
            if dates:
                return dates

    # Look for meta tags with date info
    for meta in soup.find_all("meta"):
        prop = (meta.get("property") or meta.get("name") or "").lower()
        content = meta.get("content") or ""
        if "published" in prop and content:
            result["published"] = _parse_date_str(content)
        elif "death" in prop and content:
            result["death"] = _parse_date_str(content)

    return result


def parse_funeral_home(soup):
    """
    Extract the funeral home name from an individual obituary page.

    Args:
        soup: BeautifulSoup object of the obituary page.

    Returns:
        Funeral home name string, or None if not found.
    """
    FH_SELECTORS = [
        "[data-testid='funeral-home-name']",
        ".funeral-home-name",
        "a[href*='funeral-home']",
        ".fh-name",
    ]

    for selector in FH_SELECTORS:
        el = soup.select_one(selector)
        if el:
            return el.get_text(strip=True)

    return None


def parse_obit_text(soup):
    """
    Extract the full obituary text from an individual obituary page.

    Strips all HTML tags, returns plain text.

    Args:
        soup: BeautifulSoup object of the obituary page.

    Returns:
        Full obituary text string, or empty string if not found.
    """
    TEXT_SELECTORS = [
        "[data-testid='obit-text']",
        ".obituary-text",
        ".obit-body",
        ".obituary-body",
        "article",
    ]

    for selector in TEXT_SELECTORS:
        el = soup.select_one(selector)
        if el:
            return el.get_text(separator=" ", strip=True)

    return ""


# --- Name splitting utility ---

def split_name(full_name):
    """
    Split a full name into first, middle, last, and suffix components.

    Handles common suffixes (Jr, Sr, III, etc.) and best-effort splitting:
    first token = first_name, last token = last_name, middle tokens = middle_name.

    Args:
        full_name: Full name string (e.g., "John Michael Smith Jr.").

    Returns:
        Dict with keys: first_name, middle_name, last_name, name_suffix.
        Missing parts are empty strings.
    """
    result = {
        "first_name": "",
        "middle_name": "",
        "last_name": "",
        "name_suffix": "",
    }

    if not full_name:
        return result

    # Clean up the name
    name = full_name.strip()
    # Remove commas that sometimes appear before suffixes
    name = name.replace(",", " ")
    parts = name.split()

    if not parts:
        return result

    # Check last token for suffix
    if len(parts) > 1 and parts[-1].rstrip(".").lower() in NAME_SUFFIXES:
        result["name_suffix"] = parts.pop()

    if len(parts) == 1:
        result["first_name"] = parts[0]
    elif len(parts) == 2:
        result["first_name"] = parts[0]
        result["last_name"] = parts[1]
    else:
        # First token = first, last token = last, everything in between = middle
        result["first_name"] = parts[0]
        result["last_name"] = parts[-1]
        result["middle_name"] = " ".join(parts[1:-1])

    return result


# --- Internal helpers ---

def _deep_get(data, *keys):
    """
    Safely traverse nested dicts by key path.

    Args:
        data: Root dict.
        *keys: Sequence of keys to traverse.

    Returns:
        Value at the nested path, or None if any key is missing.
    """
    for key in keys:
        if not isinstance(data, dict):
            return None
        data = data.get(key)
    return data


def _parse_date_str(date_str):
    """
    Parse a date string into YYYY-MM-DD format.

    Handles ISO 8601, common US formats, and Legacy.com date strings.

    Args:
        date_str: Date string to parse, or None.

    Returns:
        Date string in YYYY-MM-DD format, or None if unparseable.
    """
    if not date_str:
        return None

    date_str = str(date_str).strip()

    # Common date formats to try
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%B %d, %Y",        # January 15, 2026
        "%b %d, %Y",        # Jan 15, 2026
        "%m/%d/%Y",
        "%m-%d-%Y",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str[:len(date_str)], fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    log.warning("[WARN] Could not parse date: %s", date_str)
    return None


def _parse_date_range(text):
    """
    Parse a date range string like 'January 5, 1940 - March 1, 2026'.

    Args:
        text: Text containing a date range with a separator (-, to, —).

    Returns:
        Dict with 'published' (None) and 'death' date, or None if unparseable.
    """
    # Split on common separators
    for sep in [" - ", " — ", " – ", " to "]:
        if sep in text:
            parts = text.split(sep, 1)
            return {
                "published": None,
                "death": _parse_date_str(parts[1].strip()),
            }

    return None
