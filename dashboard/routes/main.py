"""Main dashboard routes — obituary listing with filters."""

from flask import Blueprint, render_template, request

from dashboard.db import get_db

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    """Render obituary table with optional filters."""
    # Read filter params
    funeral_home = (request.args.get("funeral_home") or "").strip()
    city = (request.args.get("city") or "").strip()
    county = (request.args.get("county") or "").strip()
    state = (request.args.get("state") or "").strip()
    death_date = (request.args.get("death_date") or "").strip()

    # Build query with parameterized filters
    # Always exclude duplicates unless explicitly requested
    where_clauses = ["duplicate_of IS NULL"]
    params = []

    if funeral_home:
        where_clauses.append("funeral_home LIKE %s")
        params.append(f"%{funeral_home}%")
    if city:
        where_clauses.append("city LIKE %s")
        params.append(f"%{city}%")
    if county:
        where_clauses.append("county = %s")
        params.append(county)
    if state:
        where_clauses.append("state = %s")
        params.append(state.upper())
    if death_date:
        where_clauses.append("death_date = %s")
        params.append(death_date)

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    sql = f"""
        SELECT deceased_name, first_name, last_name, death_date, published_date,
               funeral_home, city, county, state, legacy_url, site_id
        FROM obituaries
        {where_sql}
        ORDER BY COALESCE(death_date, published_date, scraped_at) DESC
        LIMIT 2000
    """

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, params)
    obits = cursor.fetchall()
    cursor.close()

    # Get distinct values for filter dropdowns
    dropdown_sql = """
        SELECT
            GROUP_CONCAT(DISTINCT funeral_home ORDER BY funeral_home SEPARATOR '||') AS funeral_homes,
            GROUP_CONCAT(DISTINCT city ORDER BY city SEPARATOR '||') AS cities,
            GROUP_CONCAT(DISTINCT county ORDER BY county SEPARATOR '||') AS counties,
            GROUP_CONCAT(DISTINCT state ORDER BY state SEPARATOR '||') AS states
        FROM obituaries
        WHERE funeral_home IS NOT NULL OR city IS NOT NULL OR state IS NOT NULL
    """
    cursor = conn.cursor(dictionary=True)
    cursor.execute(dropdown_sql)
    dropdown_row = cursor.fetchone()
    cursor.close()

    funeral_homes = [fh for fh in (dropdown_row.get("funeral_homes") or "").split("||") if fh]
    cities = [c for c in (dropdown_row.get("cities") or "").split("||") if c]
    counties = [c for c in (dropdown_row.get("counties") or "").split("||") if c]
    states = [s for s in (dropdown_row.get("states") or "").split("||") if s]

    return render_template(
        "index.html",
        obits=obits,
        total=len(obits),
        funeral_homes=funeral_homes,
        cities=cities,
        counties=counties,
        states=states,
        filters={
            "funeral_home": funeral_home,
            "city": city,
            "county": county,
            "state": state,
            "death_date": death_date,
        },
    )
