"""Dashboard configuration — reads DB credentials from AWS Secrets Manager or env."""

import os

from dotenv import load_dotenv

load_dotenv()

# Import here so aws_secrets module is available
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.aws_secrets import get_db_creds

_creds = get_db_creds()


class Config:
    DB_HOST = _creds["DB_HOST"]
    DB_PORT = int(_creds["DB_PORT"])
    DB_USER = _creds["DB_USER"]
    DB_PASSWORD = _creds["DB_PASSWORD"]
    DB_NAME = _creds["DB_NAME"]
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key-change-in-prod")
