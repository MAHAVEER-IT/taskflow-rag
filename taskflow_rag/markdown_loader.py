"""Markdown loading and section extraction for TaskFlow KB articles."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from langchain_core.documents import Document


logger = logging.getLogger(__name__)
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


def source_path(markdown_file: Path, kb_dir: Path) -> str:
    """Return canonical metadata source paths like kb/reset-password.md."""

    try:
        return f"kb/{markdown_file.relative_to(kb_dir).as_posix()}"
    except ValueError:
        return markdown_file.as_posix()


def extract_markdown_sections(markdown_text: str) -> list[tuple[str, str]]:
    """Split Markdown into heading-aware sections while preserving headings."""

    matches = list(HEADING_PATTERN.finditer(markdown_text))
    if not matches:
        stripped_text = markdown_text.strip()
        return [("General", stripped_text)] if stripped_text else []

    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown_text)
        heading = match.group(2).strip()
        section_text = markdown_text[start:end].strip()

        if section_text:
            sections.append((heading, section_text))

    return sections


def load_markdown_documents(kb_dir: Path) -> tuple[list[Document], int]:
    """Read all .md files recursively and convert sections to LangChain documents."""

    markdown_files = sorted(kb_dir.rglob("*.md"))
    section_documents: list[Document] = []

    for markdown_file in markdown_files:
        try:
            markdown_text = markdown_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            logger.exception("Unable to read %s as UTF-8. Skipping file.", markdown_file)
            continue
        except OSError:
            logger.exception("Unable to read %s. Skipping file.", markdown_file)
            continue

        for section_heading, section_text in extract_markdown_sections(markdown_text):
            section_documents.append(
                Document(
                    page_content=section_text,
                    metadata={
                        "article": markdown_file.name,
                        "section": section_heading,
                        "source": source_path(markdown_file, kb_dir),
                    },
                )
            )

    return section_documents, len(markdown_files)
