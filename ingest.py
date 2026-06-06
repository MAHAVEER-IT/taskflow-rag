"""Command-line entry point for TaskFlow KB ingestion."""

from __future__ import annotations

import logging

from taskflow_rag.pipeline import run_ingestion


logger = logging.getLogger(__name__)


def main() -> None:
    """Run ingestion and convert unexpected failures into a non-zero exit."""

    try:
        run_ingestion()
    except Exception as exc:
        logger.exception("Ingestion failed: %s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
