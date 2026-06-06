"""Retrieve relevant TaskFlow KB chunks from the persisted ChromaDB store."""

from __future__ import annotations

import argparse
import logging
from typing import Any

from taskflow_rag.config import load_config
from taskflow_rag.embeddings import create_embedding_function
from taskflow_rag.logging_config import configure_logging
from taskflow_rag.vector_store import count_vectors, get_vector_store


DEFAULT_TOP_K = 3
logger = logging.getLogger(__name__)


def validate_question(question: str) -> str:
    """Return a cleaned user question or fail with a helpful error."""

    cleaned_question = question.strip()
    if not cleaned_question:
        raise ValueError("Question cannot be empty.")
    return cleaned_question


def validate_vector_database_exists() -> None:
    """Fail early when the local ChromaDB directory has not been created."""

    config = load_config()
    if not config.persist_directory.exists():
        raise FileNotFoundError(
            f"ChromaDB directory not found: {config.persist_directory}. "
            "Run python ingest.py before retrieval."
        )


def format_result(document: Any, score: float) -> dict[str, Any]:
    """Convert a LangChain Document and score into API-friendly output."""

    metadata = document.metadata or {}
    return {
        "content": document.page_content,
        "article": metadata.get("article", "unknown"),
        "section": metadata.get("section", "unknown"),
        "source": metadata.get("source", "unknown"),
        "chunk_id": metadata.get("chunk_id", "unknown"),
        "score": round(float(score), 4),
    }


def retrieve(question: str, top_k: int = DEFAULT_TOP_K) -> list[dict[str, Any]]:
    """Search ChromaDB and return the most relevant KB chunks.

    Scores come from LangChain's relevance-score helper, where higher is better
    and values are typically normalized between 0 and 1.
    """

    cleaned_question = validate_question(question)
    config = load_config()

    if not config.persist_directory.exists():
        raise FileNotFoundError(
            f"ChromaDB directory not found: {config.persist_directory}. "
            "Run python ingest.py before retrieval."
        )

    embeddings = create_embedding_function(
        model=config.embedding_model,
        google_api_key=config.google_api_key,
    )
    vector_store = get_vector_store(
        persist_directory=config.persist_directory,
        collection_name=config.collection_name,
        embeddings=embeddings,
    )

    vector_count = count_vectors(vector_store)
    if vector_count == 0:
        raise RuntimeError(
            f"Collection '{config.collection_name}' is empty. Run python ingest.py first."
        )

    logger.info("Searching %s vectors in collection '%s'.", vector_count, config.collection_name)
    matches = vector_store.similarity_search_with_relevance_scores(cleaned_question, k=top_k)

    if not matches:
        return []

    return [format_result(document, score) for document, score in matches]


def print_results(results: list[dict[str, Any]]) -> None:
    """Print retrieval results in a readable CLI format."""

    if not results:
        print("\nNo matching documents found.")
        return

    print("\nTop Results")
    for result in results:
        print()
        print(f"Article: {result['article']}")
        print(f"Section: {result['section']}")
        print(f"Score: {result['score']:.2f}")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for ad hoc retrieval testing."""

    parser = argparse.ArgumentParser(description="Search the TaskFlow KB vector store.")
    parser.add_argument("question", nargs="*", help="Question to search for.")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K, help="Number of chunks to return.")
    return parser.parse_args()


def main() -> None:
    """CLI entry point for testing retrieval."""

    configure_logging()
    args = parse_args()
    question = " ".join(args.question).strip() or input("Ask a question: ").strip()

    try:
        results = retrieve(question=question, top_k=args.top_k)
        print_results(results)
    except Exception as exc:
        logger.exception("Retrieval failed: %s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
