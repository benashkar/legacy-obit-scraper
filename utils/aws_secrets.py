"""
Fetch DB credentials from AWS Secrets Manager, falling back to env vars.

Secret name: cr-obituaries/db99
Expected JSON keys: DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

On Render/production: boto3 fetches from AWS (needs AWS_ACCESS_KEY_ID,
AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION in env).
Locally: falls back to .env file via python-dotenv.
"""

import json
import os

from utils.logger import get_logger

log = get_logger(__name__)

SECRET_NAME = "ben/ai-tool/db99"
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

_cached_creds = None


def get_db_creds():
    """Return dict with DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME.

    Tries AWS Secrets Manager first, falls back to env vars.
    Caches the result after the first successful fetch.
    """
    global _cached_creds
    if _cached_creds is not None:
        return _cached_creds

    creds = _fetch_from_aws()
    if creds:
        _cached_creds = creds
        return creds

    log.info("[OK] AWS Secrets Manager unavailable, using env vars")
    creds = {
        "DB_HOST": os.getenv("DB_HOST", "localhost"),
        "DB_PORT": os.getenv("DB_PORT", "3306"),
        "DB_USER": os.getenv("DB_USER", ""),
        "DB_PASSWORD": os.getenv("DB_PASSWORD", ""),
        "DB_NAME": os.getenv("DB_NAME", ""),
    }
    _cached_creds = creds
    return creds


def _fetch_from_aws():
    """Try to fetch secret from AWS Secrets Manager. Returns dict or None."""
    try:
        import boto3
        client = boto3.client("secretsmanager", region_name=AWS_REGION)
        resp = client.get_secret_value(SecretId=SECRET_NAME)
        secret = json.loads(resp["SecretString"])
        log.info("[OK] Loaded DB credentials from AWS Secrets Manager")
        return {
            "DB_HOST": secret.get("DB_HOST") or "",
            "DB_PORT": secret.get("DB_PORT") or "3306",
            "DB_USER": secret.get("DB_USER") or "",
            "DB_PASSWORD": secret.get("DB_PASSWORD") or "",
            "DB_NAME": secret.get("DB_NAME") or "",
        }
    except ImportError:
        return None
    except Exception as exc:
        log.info("[--] AWS Secrets Manager fetch failed: %s", exc)
        return None
