"""Shared data models for ingestion."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IngestionStats:
    """Summary values printed after a successful ingestion run."""

    total_files_processed: int
    total_chunks_created: int
    total_vectors_stored: int
