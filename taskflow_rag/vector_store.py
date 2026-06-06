"""ChromaDB access helpers."""

from __future__ import annotations

from pathlib import Path

import chromadb
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings


def get_vector_store(
    persist_directory: Path,
    collection_name: str,
    embeddings: GoogleGenerativeAIEmbeddings,
) -> Chroma:
    """Create or open the persistent Chroma collection."""

    client = chromadb.PersistentClient(path=str(persist_directory))
    return Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=embeddings,
    )


def count_vectors(vector_store: Chroma) -> int:
    """Return the current vector count for the Chroma collection."""

    return vector_store._collection.count()
