"""Document chunking utilities."""

from __future__ import annotations

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_documents(
    section_documents: list[Document],
    chunk_size: int,
    chunk_overlap: int,
) -> list[Document]:
    """Chunk section documents and add deterministic chunk IDs to metadata."""

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )

    chunks = splitter.split_documents(section_documents)
    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = f"{chunk.metadata['article']}:{index:04d}"

    return chunks
