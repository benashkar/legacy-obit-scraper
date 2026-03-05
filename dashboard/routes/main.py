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
        SELECT deceased_name, first_name, last_name, birth_date, death_date,
               published_date, funeral_home, city, county, state, legacy_url,
               site_id
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

    # Get distinct values for filter dropdowns (separate fast queries)
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT state FROM obituaries WHERE state IS NOT NULL AND state != '' ORDER BY state")
    states = [r[0] for r in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT county FROM obituaries WHERE county IS NOT NULL AND county != '' ORDER BY county LIMIT 500")
    counties = [r[0] for r in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT city FROM obituaries WHERE city IS NOT NULL AND city != '' ORDER BY city LIMIT 500")
    cities = [r[0] for r in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT funeral_home FROM obituaries WHERE funeral_home IS NOT NULL AND funeral_home != '' ORDER BY funeral_home LIMIT 500")
    funeral_homes = [r[0] for r in cursor.fetchall()]

    cursor.close()

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
