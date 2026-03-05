"""Per-request MySQL connection for Flask dashboard."""

import mysql.connector
from flask import current_app, g


def get_db():
    """Get or create a MySQL connection for the current request."""
    if "db" not in g:
        cfg = current_app.config
        g.db = mysql.connector.connect(
            host=cfg["DB_HOST"],
            port=cfg["DB_PORT"],
            user=cfg["DB_USER"],
            password=cfg["DB_PASSWORD"],
            database=cfg["DB_NAME"],
            charset="utf8mb4",
        )
    return g.db


def close_db(exc=None):
    """Close the DB connection at end of request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()
