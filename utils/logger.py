"""
Logging utility for the Legacy obituary scraper.

Windows-safe output: uses [OK], [ERR], [WARN] prefixes instead of Unicode symbols.
"""

import logging
import sys


def get_logger(name):
    """
    Create and return a configured logger instance.

    Args:
        name: Logger name, typically __name__ of the calling module.

    Returns:
        logging.Logger configured with stdout handler and standard format.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)

        # Windows-safe format: [OK]/[ERR]/[WARN] prefixes, no Unicode symbols
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)-5s] %(name)s — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
