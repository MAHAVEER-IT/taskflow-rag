"""Configuration helpers for the TaskFlow ingestion pipeline."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
DEFAULT_COLLECTION_NAME = "taskflow_kb"
DEFAULT_PERSIST_DIRECTORY = "./chroma_db"
DEFAULT_KB_DIRECTORY = "./kb"
DEFAULT_EMBEDDING_MODEL = "models/gemini-embedding-001"
PLACEHOLDER_API_KEYS = {
    "your_gemini_api_key_here",
    "replace_with_your_gemini_api_key",
}


@dataclass(frozen=True)
class IngestionConfig:
    """Resolved runtime settings for a single ingestion run."""

    kb_dir: Path
    persist_directory: Path
    collection_name: str
    embedding_model: str
    google_api_key: str
    chunk_size: int = CHUNK_SIZE
    chunk_overlap: int = CHUNK_OVERLAP


def project_dir() -> Path:
    """Return the RAG_MODEL project directory."""

    return Path(__file__).resolve().parents[1]


def resolve_project_path(configured_path: str) -> Path:
    """Resolve relative paths from the RAG_MODEL project directory."""

    path = Path(configured_path)
    if not path.is_absolute():
        path = project_dir() / path
    return path.resolve()


def resolve_kb_directory(configured_path: str) -> Path:
    """Resolve the KB folder and tolerate older uppercase KB naming."""

    kb_dir = resolve_project_path(configured_path)
    if kb_dir.exists():
        return kb_dir

    uppercase_kb_dir = kb_dir.parent / "KB"
    if uppercase_kb_dir.exists():
        return uppercase_kb_dir.resolve()

    return kb_dir


def load_config() -> IngestionConfig:
    """Load .env values and return validated ingestion configuration."""

    load_dotenv(project_dir() / ".env")

    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key or google_api_key.strip() in PLACEHOLDER_API_KEYS:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Copy .env.example to .env and add your Gemini API key."
        )

    return IngestionConfig(
        kb_dir=resolve_kb_directory(os.getenv("KB_DIRECTORY", DEFAULT_KB_DIRECTORY)),
        persist_directory=resolve_project_path(
            os.getenv("CHROMA_PERSIST_DIRECTORY", DEFAULT_PERSIST_DIRECTORY)
        ),
        collection_name=os.getenv("CHROMA_COLLECTION_NAME", DEFAULT_COLLECTION_NAME),
        embedding_model=os.getenv("GEMINI_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL),
        google_api_key=google_api_key,
    )
