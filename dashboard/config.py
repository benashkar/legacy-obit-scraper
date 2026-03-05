"""Dashboard configuration — reads DB credentials from AWS Secrets Manager or env."""

import os
import traceback

from dotenv import load_dotenv

load_dotenv()

try:
    from utils.aws_secrets import get_db_creds
    _creds = get_db_creds()
except Exception:
    traceback.print_exc()
    _creds = {
        "DB_HOST": os.getenv("DB_HOST", "localhost"),
        "DB_PORT": os.getenv("DB_PORT", "3306"),
        "DB_USER": os.getenv("DB_USER", ""),
        "DB_PASSWORD": os.getenv("DB_PASSWORD", ""),
        "DB_NAME": os.getenv("DB_NAME", ""),
    }


class Config:
    DB_HOST = _creds["DB_HOST"]
    DB_PORT = int(_creds.get("DB_PORT") or "3306")
    DB_USER = _creds["DB_USER"]
    DB_PASSWORD = _creds["DB_PASSWORD"]
    DB_NAME = _creds.get("DB_NAME") or os.getenv("DB_NAME", "")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key-change-in-prod")
