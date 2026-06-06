"""Orchestration for the TaskFlow Knowledge Base ingestion pipeline."""

from __future__ import annotations

import logging

from taskflow_rag.chunking import split_documents
from taskflow_rag.config import IngestionConfig, load_config
from taskflow_rag.embeddings import create_embedding_function
from taskflow_rag.logging_config import configure_logging
from taskflow_rag.markdown_loader import load_markdown_documents
from taskflow_rag.models import IngestionStats
from taskflow_rag.vector_store import count_vectors, get_vector_store


logger = logging.getLogger(__name__)


def validate_kb(config: IngestionConfig) -> None:
    """Fail early when the configured KB folder is missing."""

    if not config.kb_dir.exists():
        raise FileNotFoundError(f"KB directory not found: {config.kb_dir}")


def print_skip_summary(collection_name: str, existing_vectors: int) -> None:
    """Print duplicate-ingestion skip details for the operator."""

    print("\nIngestion skipped: existing vectors found.")
    print(f"Collection: {collection_name}")
    print(f"Vectors already stored: {existing_vectors}")


def print_success_summary(stats: IngestionStats) -> None:
    """Print ingestion statistics after vectors are stored."""

    print("\nIngestion completed successfully.")
    print(f"Total files processed: {stats.total_files_processed}")
    print(f"Total chunks created: {stats.total_chunks_created}")
    print(f"Total vectors stored: {stats.total_vectors_stored}")


def run_ingestion() -> IngestionStats | None:
    """Run the full KB ingestion workflow."""

    configure_logging()
    config = load_config()
    validate_kb(config)

    logger.info("Starting TaskFlow KB ingestion.")
    logger.info("KB directory: %s", config.kb_dir)
    logger.info("Chroma persist directory: %s", config.persist_directory)
    logger.info("Chroma collection: %s", config.collection_name)

    embeddings = create_embedding_function(
        model=config.embedding_model,
        google_api_key=config.google_api_key,
    )
    vector_store = get_vector_store(
        persist_directory=config.persist_directory,
        collection_name=config.collection_name,
        embeddings=embeddings,
    )

    existing_vectors = count_vectors(vector_store)
    if existing_vectors > 0:
        logger.info(
            "Skipping ingestion. Collection '%s' already contains %s vectors.",
            config.collection_name,
            existing_vectors,
        )
        print_skip_summary(config.collection_name, existing_vectors)
        return None

    section_documents, total_files = load_markdown_documents(config.kb_dir)
    if total_files == 0:
        raise FileNotFoundError(f"No Markdown files found in {config.kb_dir}")

    if not section_documents:
        raise RuntimeError(
            f"Markdown files were found in {config.kb_dir}, but no content was loaded."
        )

    chunks = split_documents(
        section_documents=section_documents,
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )
    if not chunks:
        raise RuntimeError("No chunks were created from the loaded Markdown documents.")

    ids = [chunk.metadata["chunk_id"] for chunk in chunks]
    logger.info("Embedding and storing %s chunks. This may take a moment.", len(chunks))
    vector_store.add_documents(documents=chunks, ids=ids)

    stats = IngestionStats(
        total_files_processed=total_files,
        total_chunks_created=len(chunks),
        total_vectors_stored=count_vectors(vector_store),
    )
    print_success_summary(stats)
    return stats
