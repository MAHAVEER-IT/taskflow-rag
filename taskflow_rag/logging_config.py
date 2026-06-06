"""Logging setup for ingestion commands."""

from __future__ import annotations

import logging


def configure_logging() -> None:
    """Configure readable console logging once."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
