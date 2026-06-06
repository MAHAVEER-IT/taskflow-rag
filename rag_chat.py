"""Interactive TaskFlow Support Assistant powered by Chroma retrieval + Gemini."""

from __future__ import annotations

import logging
import os
import argparse
from typing import Any

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from retrieve import DEFAULT_TOP_K, retrieve
from taskflow_rag.config import PLACEHOLDER_API_KEYS, project_dir
from taskflow_rag.logging_config import configure_logging


CONFIDENCE_THRESHOLD = 0.55
DEFAULT_CHAT_MODEL = "gemini-2.5-flash"
logger = logging.getLogger(__name__)


PROMPT_TEMPLATE = """You are a customer support assistant for TaskFlow.

Rules:
1. Answer ONLY using provided context.
2. Do not make up information.
3. If information is missing, say you cannot find it.
4. Always cite article and section.
5. Be concise and professional.

Context:
{retrieved_chunks}

Question:
{user_question}
"""


def load_api_key() -> str:
    """Load and validate the Gemini API key for answer generation."""

    load_dotenv(project_dir() / ".env")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key.strip() in PLACEHOLDER_API_KEYS:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Copy .env.example to .env and add your Gemini API key."
        )
    return api_key


def create_chat_model() -> ChatGoogleGenerativeAI:
    """Create the Gemini chat model used for grounded answer generation."""

    api_key = load_api_key()
    model = os.getenv("GEMINI_CHAT_MODEL", DEFAULT_CHAT_MODEL)
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=0.2,
    )


def highest_score(results: list[dict[str, Any]]) -> float:
    """Return the best retrieval score, or 0 when no results exist."""

    if not results:
        return 0.0
    return max(float(result.get("score", 0.0)) for result in results)


def build_context(results: list[dict[str, Any]]) -> str:
    """Format retrieved chunks for the Gemini prompt with source metadata."""

    context_blocks: list[str] = []
    for index, result in enumerate(results, start=1):
        context_blocks.append(
            "\n".join(
                [
                    f"[Chunk {index}]",
                    f"Article: {result['article']}",
                    f"Section: {result['section']}",
                    f"Score: {result['score']:.2f}",
                    "Content:",
                    result["content"],
                ]
            )
        )
    return "\n\n---\n\n".join(context_blocks)


def unique_citations(results: list[dict[str, Any]]) -> list[str]:
    """Build stable article > section citations from retrieved chunks."""

    citations: list[str] = []
    seen: set[tuple[str, str]] = set()

    for result in results:
        citation_key = (str(result["article"]), str(result["section"]))
        if citation_key in seen:
            continue
        seen.add(citation_key)
        citations.append(f"{result['article']} > {result['section']}")

    return citations


def escalation_message(score: float) -> str:
    """Return the low-confidence support escalation response."""

    return (
        "I couldn't find a reliable answer in the knowledge base.\n\n"
        "Would you like me to create a support ticket?\n\n"
        f"Confidence Score: {score:.2f}"
    )


def normalize_model_text(content: Any) -> str:
    """Convert Gemini response content into a printable string."""

    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        return "\n".join(str(item) for item in content).strip()
    return str(content).strip()


def generate_answer(question: str, results: list[dict[str, Any]]) -> str:
    """Call Gemini with retrieved context and append citations."""

    context = build_context(results)
    prompt = PROMPT_TEMPLATE.format(
        retrieved_chunks=context,
        user_question=question.strip(),
    )

    chat_model = create_chat_model()
    response = chat_model.invoke(prompt)
    answer = normalize_model_text(response.content)
    citations = "\n".join(unique_citations(results))

    if "Source:" in answer:
        return answer

    return f"{answer}\n\nSource:\n{citations}"


def answer_question(question: str, top_k: int = DEFAULT_TOP_K) -> tuple[str, float]:
    """Retrieve context, enforce confidence, and generate a grounded answer."""

    results = retrieve(question=question, top_k=top_k)
    score = highest_score(results)

    if not results:
        return escalation_message(score), score

    if score < CONFIDENCE_THRESHOLD:
        return escalation_message(score), score

    try:
        return generate_answer(question=question, results=results), score
    except Exception as exc:
        logger.exception("Gemini answer generation failed: %s", exc)
        return (
            "I found relevant knowledge base content, but I could not generate an answer right now. "
            "Please try again or contact support.",
            score,
        )


def answer_question_with_metadata(question: str, top_k: int = DEFAULT_TOP_K) -> dict[str, Any]:
    """Return an API-ready answer payload with sources and escalation status."""

    results = retrieve(question=question, top_k=top_k)
    score = highest_score(results)
    sources = unique_citations(results)

    if not results or score < CONFIDENCE_THRESHOLD:
        return {
            "answer": "I couldn't find a reliable answer.",
            "sources": sources,
            "confidence": round(score, 4),
            "escalate": True,
        }

    try:
        answer = generate_answer(question=question, results=results)
    except Exception as exc:
        logger.exception("Gemini answer generation failed: %s", exc)
        raise RuntimeError("Gemini answer generation failed.") from exc

    return {
        "answer": answer,
        "sources": sources,
        "confidence": round(score, 4),
        "escalate": False,
    }


def print_final_response(answer: str, score: float) -> None:
    """Print the final assistant response exactly as CLI users should review it."""

    print()
    print("Answer:")
    print(answer)
    print()
    print("Confidence:")
    print(f"{score:.2f}")
    print()


def run_single_question(question: str, top_k: int) -> None:
    """Run one question through retrieval + Gemini and exit."""

    answer, score = answer_question(question=question, top_k=top_k)
    print_final_response(answer, score)


def run_chat(top_k: int = DEFAULT_TOP_K) -> None:
    """Run an interactive command-line support assistant."""

    print("TaskFlow Support Assistant")
    print()

    while True:
        question = input("Ask a question: ").strip()
        if question.lower() in {"exit", "quit", "q"}:
            print("Goodbye.")
            return
        if not question:
            print("Please enter a question.")
            print()
            continue

        try:
            answer, score = answer_question(question=question, top_k=top_k)
        except Exception as exc:
            logger.exception("Chat failed: %s", exc)
            print(f"Error: {exc}")
            print()
            continue

        print_final_response(answer, score)


def parse_args() -> argparse.Namespace:
    """Parse CLI options for interactive or one-shot testing."""

    parser = argparse.ArgumentParser(description="Run the TaskFlow Support Assistant.")
    parser.add_argument(
        "question",
        nargs="*",
        help="Optional one-shot question. If omitted, interactive chat mode starts.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=DEFAULT_TOP_K,
        help="Number of retrieved chunks to send to Gemini.",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entry point."""

    configure_logging()
    args = parse_args()
    question = " ".join(args.question).strip()

    if question:
        run_single_question(question=question, top_k=args.top_k)
        return

    run_chat(top_k=args.top_k)


if __name__ == "__main__":
    main()
