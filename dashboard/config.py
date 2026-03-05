"""Dashboard configuration — reads DB credentials from env vars.

On Render: env vars are set via Render API (host, port, user, password from AWS
Secrets Manager values; DB_NAME is project-specific).
Locally: loaded from .env via python-dotenv.
"""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key-change-in-prod")
