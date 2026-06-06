"""Embedding provider setup."""

from __future__ import annotations

from langchain_google_genai import GoogleGenerativeAIEmbeddings


def create_embedding_function(
    model: str,
    google_api_key: str,
) -> GoogleGenerativeAIEmbeddings:
    """Create the Gemini embedding client used by Chroma."""

    return GoogleGenerativeAIEmbeddings(
        model=model,
        google_api_key=google_api_key,
    )
