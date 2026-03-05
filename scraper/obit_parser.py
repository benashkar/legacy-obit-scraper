"""
Stateless parsing functions for Legacy.com obituary data.

Three extraction strategies (tried in order):
  1. Embedded JSON in <script type="application/json"><!--{...}--></script>
     Data path: obituaryList.obituaries (current Legacy.com 2026 format)
  2. window.__INITIAL_STATE__ JSON (older Legacy.com format, ahplummer pattern)
  3. BeautifulSoup HTML fallback for individual obituary pages

Name fields use structured data from Legacy.com when available:
  name.firstName, name.middleName, name.lastName, name.suffix, name.fullName
Falls back to split_name() for best-effort parsing when structured data missing.
"""

import html as html_module
import json
import re
from datetime import datetime

from bs4 import BeautifulSoup

from scraper.date_extractor import extract_dates_from_text
from utils.logger import get_logger

log = get_logger(__name__)

# Regex to extract __INITIAL_STATE__ JSON from script tags (older pattern)
INITIAL_STATE_PATTERN = re.compile(
    r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\})\s*;",
    re.DOTALL,
)

# Common name suffixes to detect and separate
NAME_SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v", "esq", "phd", "md", "dds"}


def extract_obits_from_listing(html_text):
    """
    Extract obituary entries from a Legacy.com listing page.

    Tries embedded JSON first (2026 format), then __INITIAL_STATE__ (older),
    then HTML link fallback.

    Args:
        html_text: Raw HTML string of the listing page.

    Returns:
        List of dicts, each with keys:
            - url: Full obituary page URL
            - deceased_name: Full name string
            - first_name, middle_name, last_name, name_suffix: Parsed name parts
            - obit_text: Obituary snippet (may be truncated from listing)
            - published_date: Date string (YYYY-MM-DD) or None
            - death_date: Date string or None
            - funeral_home: Funeral home name or None
    """
    # Strategy 1: Embedded JSON in <script type="application/json"> (current 2026 format)
    # Legacy.com wraps JSON in HTML comments: <!--{...}-->
    obits = _extract_from_embedded_json(html_text)
    if obits:
        return obits

    # Strategy 2: window.__INITIAL_STATE__ (older Legacy.com pattern)
    obits = _extract_from_initial_state(html_text)
    if obits:
        return obits

    # Strategy 3: HTML link fallback
    return _extract_from_html(html_text)


def _extract_from_embedded_json(html_text):
    """
    Parse obituary data from the embedded JSON in <script type="application/json">.

    Current Legacy.com (2026) embeds a large JSON blob wrapped in HTML comments
    inside a script tag. The obituary list is at obituaryList.obituaries.

    Each obituary entry has rich structured data including:
      - name: {firstName, middleName, lastName, suffix, fullName, nickName}
      - funeralHome: {id, name}
      - links: {obituaryUrl: {href, path}}
      - obitSnippet: truncated text
      - datePostedFrom/datePostedTo: ISO datetime strings
      - location: {city: {fullName}, state: {code, fullName}}

    Args:
        html_text: Raw HTML string.

    Returns:
        List of obit dicts, or empty list if pattern not found.
    """
    soup = BeautifulSoup(html_text, "lxml")

    # Find all application/json script tags and look for the large one
    json_scripts = soup.find_all("script", type="application/json")

    for script in json_scripts:
        content = (script.string or "").strip()

        # Skip scripts that clearly aren't obituary data
        if len(content) < 100:
            continue

        # Strip HTML comment markers: <!--{...}-->
        if content.startswith("<!--"):
            content = content[4:]
        if content.endswith("-->"):
            content = content[:-3]
        content = content.strip()

        # Unescape HTML entities (Legacy.com encodes &amp; etc. inside the JSON)
        content = html_module.unescape(content)

        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            log.warning("[WARN] Failed to parse embedded JSON: %s", exc)
            continue

        # Look for obituaryList.obituaries (primary path)
        obit_list = _deep_get(data, "obituaryList", "obituaries")

        if not obit_list or not isinstance(obit_list, list):
            # Try alternate paths
            for key in data:
                val = data[key]
                if isinstance(val, dict) and "obituaries" in val:
                    candidate = val["obituaries"]
                    if isinstance(candidate, list) and len(candidate) > 0:
                        # Verify it has obit-like structure (has personId or name)
                        first = candidate[0]
                        if isinstance(first, dict) and ("personId" in first or "name" in first):
                            obit_list = candidate
                            break

        if not obit_list:
            continue

        log.info("[OK] Found %d obituaries in embedded JSON", len(obit_list))
        return _parse_obit_list_entries(obit_list)

    return []


def _parse_obit_list_entries(obit_list):
    """
    Convert Legacy.com obituaryList entries to standardized obit dicts.

    Args:
        obit_list: List of raw obituary dicts from Legacy.com JSON.

    Returns:
        List of standardized obit dicts.
    """
    obits = []
    for entry in obit_list:
        # Extract name from structured name object
        name_obj = entry.get("name") or {}

        first = name_obj.get("firstName") or ""
        middle = name_obj.get("middleName") or ""
        last = name_obj.get("lastName") or ""
        suffix = name_obj.get("suffix") or ""
        full_name = name_obj.get("fullName") or f"{first} {last}".strip()

        # Build the obit URL from links.obituaryUrl.href
        links = entry.get("links") or {}
        obit_url_obj = links.get("obituaryUrl") or {}
        url = obit_url_obj.get("href") or ""
        if url and not url.startswith("http"):
            url = f"https://www.legacy.com{url}"

        # Extract funeral home name
        fh_obj = entry.get("funeralHome") or {}
        funeral_home = fh_obj.get("name") or entry.get("publisherName")

        # Parse dates — datePostedFrom is the reliable published date (ISO format)
        published_date = _parse_date_str(entry.get("datePostedFrom"))
        # Obituary snippet (truncated text from listing page)
        obit_text = entry.get("obitSnippet") or ""

        # Extract birth and death dates from the obit text
        dates_from_text = extract_dates_from_text(obit_text)
        death_date = dates_from_text["death_date"]
        birth_date = dates_from_text["birth_date"]

        # Extract city and state from location object
        loc_obj = entry.get("location") or {}
        city_obj = loc_obj.get("city") or {}
        state_obj = loc_obj.get("state") or {}
        city = city_obj.get("fullName") or ""
        state = state_obj.get("code") or ""

        obits.append({
            "url": url,
            "deceased_name": full_name,
            "first_name": first,
            "middle_name": middle,
            "last_name": last,
            "name_suffix": suffix,
            "obit_text": obit_text,
            "published_date": published_date,
            "death_date": death_date,
            "birth_date": birth_date,
            "funeral_home": funeral_home,
            "city": city,
            "state": state,
        })

    return obits


def _extract_from_initial_state(html_text):
    """
    Parse obituary data from the window.__INITIAL_STATE__ JSON blob.

    Older Legacy.com pattern (pre-2024) where data is embedded in a script tag
    as a JavaScript variable assignment.

    Args:
        html_text: Raw HTML string.

    Returns:
        List of obit dicts, or empty list if pattern not found.
    """
    match = INITIAL_STATE_PATTERN.search(html_text)
    if not match:
        return []

    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        log.warning("[WARN] Failed to parse __INITIAL_STATE__ JSON: %s", exc)
        return []

    # Navigate to the obituary edges — path from ahplummer/LegacyObituaries
    edges = _deep_get(
        data, "BrowseStore", "data", "obituaries", "obituaries", "edges"
    )
    if not edges:
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

        parsed = split_name(full_name)

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
            "city": "",
            "state": "",
        })

    return obits


def _extract_from_html(html_text):
    """
    Fallback: extract obituary links from HTML using BeautifulSoup selectors.

    Less reliable than JSON extraction — selectors may change. Returns partial
    data (URL and name only); full details fetched from individual obit pages.

    Args:
        html_text: Raw HTML string.

    Returns:
        List of obit dicts with url and deceased_name populated.
    """
    soup = BeautifulSoup(html_text, "lxml")

    # Try multiple selector patterns for robustness
    CARD_SELECTORS = [
        "a[href*='/us/obituaries/name/']",
        "a[data-testid='obituary-card']",
        "a.obit-card",
        "div.obituary-list a[href*='/obituary/']",
    ]

    links = []
    for selector in CARD_SELECTORS:
        links = soup.select(selector)
        if links:
            break

    if not links:
        log.warning("[WARN] HTML fallback found no obituary links")
        return []

    # Deduplicate by href
    seen = set()
    obits = []
    for link in links:
        href = link.get("href") or ""
        if not href or href in seen:
            continue
        seen.add(href)

        if not href.startswith("http"):
            href = f"https://www.legacy.com{href}"

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
            "city": "",
            "state": "",
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

    # Strip "on " prefix that Legacy.com uses (e.g., "on Mar. 4, 2026")
    if date_str.lower().startswith("on "):
        date_str = date_str[3:].strip()

    formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%B %d, %Y",        # January 15, 2026
        "%b %d, %Y",        # Jan 15, 2026
        "%b. %d, %Y",       # Mar. 4, 2026 (Legacy.com format)
        "%m/%d/%Y",
        "%m-%d-%Y",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    log.warning("[WARN] Could not parse date: %s", date_str)
    return None


def _parse_date_range(text):
    """
    Parse a date range string like 'January 5, 1940 - March 1, 2026'.

    Args:
        text: Text containing a date range with a separator (-, to, --).

    Returns:
        Dict with 'published' (None) and 'death' date, or None if unparseable.
    """
    for sep in [" - ", " — ", " – ", " to "]:
        if sep in text:
            parts = text.split(sep, 1)
            return {
                "published": None,
                "death": _parse_date_str(parts[1].strip()),
            }

    return None
