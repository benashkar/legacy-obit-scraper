"""
Generate markets.json for all 50 US states using Census Bureau county data.

Reads the national_county2020.txt FIPS file and generates Legacy.com-compatible
market entries for every county in all 50 states.

Slug rules:
  - Lowercase, spaces to hyphens, append "-county" (or appropriate suffix)
  - "St." / "Saint" prefixes → "saint-"
  - Remove "County", "Parish", "Borough", etc. suffixes before building slug
  - Handles special cases (e.g., DeWitt TX vs De Witt IL)
"""

import csv
import json
import os
import re

MARKETS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config",
    "markets.json",
)

COUNTY_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "counties.txt",
)

# State abbreviation → Legacy.com state slug
STATE_SLUGS = {
    "AL": "alabama", "AK": "alaska", "AZ": "arizona", "AR": "arkansas",
    "CA": "california", "CO": "colorado", "CT": "connecticut", "DE": "delaware",
    "FL": "florida", "GA": "georgia", "HI": "hawaii", "ID": "idaho",
    "IL": "illinois", "IN": "indiana", "IA": "iowa", "KS": "kansas",
    "KY": "kentucky", "LA": "louisiana", "ME": "maine", "MD": "maryland",
    "MA": "massachusetts", "MI": "michigan", "MN": "minnesota", "MS": "mississippi",
    "MO": "missouri", "MT": "montana", "NE": "nebraska", "NV": "nevada",
    "NH": "new-hampshire", "NJ": "new-jersey", "NM": "new-mexico", "NY": "new-york",
    "NC": "north-carolina", "ND": "north-dakota", "OH": "ohio", "OK": "oklahoma",
    "OR": "oregon", "PA": "pennsylvania", "RI": "rhode-island", "SC": "south-carolina",
    "SD": "south-dakota", "TN": "tennessee", "TX": "texas", "UT": "utah",
    "VT": "vermont", "VA": "virginia", "WA": "washington", "WV": "west-virginia",
    "WI": "wisconsin", "WY": "wyoming",
}

# County type suffixes to strip before building the slug
SUFFIXES_TO_STRIP = [
    " County", " Parish", " Borough", " Census Area",
    " Municipality", " city", " City and Borough",
    " City", " Municipio",
]

# Known slug overrides for tricky counties
SLUG_OVERRIDES = {
    # DeWitt variations
    ("IL", "De Witt"): "de-witt-county",
    ("TX", "DeWitt"): "dewitt-county",
}


def county_name_to_slug(raw_name):
    """Convert a Census county name to a Legacy.com URL slug."""
    name = raw_name.strip()

    # Strip suffix (County, Parish, Borough, etc.)
    base = name
    for suffix in SUFFIXES_TO_STRIP:
        if base.endswith(suffix):
            base = base[: -len(suffix)].strip()
            break

    # Handle "St." / "Saint" → "saint-"
    base = re.sub(r"^St\.\s+", "Saint ", base)

    # Lowercase, replace spaces/special chars with hyphens
    slug = base.lower()
    slug = re.sub(r"[''.]", "", slug)  # remove apostrophes and periods
    slug = re.sub(r"[^a-z0-9]+", "-", slug)  # non-alphanumeric → hyphen
    slug = slug.strip("-")

    return slug + "-county"


def display_name(raw_name):
    """Get clean county display name (without 'County'/'Parish' suffix)."""
    name = raw_name.strip()
    for suffix in SUFFIXES_TO_STRIP:
        if name.endswith(suffix):
            return name[: -len(suffix)].strip()
    return name


def main():
    # Read Census data
    counties_by_state = {}
    with open(COUNTY_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="|")
        for row in reader:
            state = row["STATE"].strip()
            county_name = row["COUNTYNAME"].strip()
            class_fp = row["CLASSFP"].strip()

            # Skip territories (only 50 states)
            if state not in STATE_SLUGS:
                continue

            # Only include actual counties (H1) and county-equivalents (H4, H5, H6)
            # Skip C7 (independent cities in VA) — Legacy.com doesn't list them as counties
            if class_fp not in ("H1", "H4", "H5", "H6"):
                continue

            if state not in counties_by_state:
                counties_by_state[state] = []
            counties_by_state[state].append(county_name)

    # Build market entries
    markets = []
    for state_abbrev in sorted(counties_by_state.keys()):
        state_slug = STATE_SLUGS[state_abbrev]
        for county_name in sorted(counties_by_state[state_abbrev]):
            display = display_name(county_name)

            # Check for slug overrides
            override_key = (state_abbrev, display)
            if override_key in SLUG_OVERRIDES:
                legacy_slug = SLUG_OVERRIDES[override_key]
            else:
                legacy_slug = county_name_to_slug(county_name)

            # Build site_id from state abbrev + county slug (minus "-county")
            county_slug_short = legacy_slug.replace("-county", "")
            site_id = f"{state_abbrev.lower()}-{county_slug_short}"

            markets.append({
                "site_id": site_id,
                "state": state_slug,
                "legacy_slug": legacy_slug,
                "type": "county",
                "county": display,
            })

    # Write markets.json
    with open(MARKETS_FILE, "w", encoding="utf-8") as f:
        json.dump(markets, f, indent=2, ensure_ascii=False)

    # Summary
    from collections import Counter
    by_state = Counter(m["state"] for m in markets)
    print(f"Total markets: {len(markets)}")
    print(f"States: {len(by_state)}")
    for state, count in sorted(by_state.items()):
        print(f"  {state}: {count}")


if __name__ == "__main__":
    main()
