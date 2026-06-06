"""FastAPI backend for the TaskFlow Support Assistant."""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

from rag_chat import answer_question_with_metadata
from taskflow_rag.logging_config import configure_logging
from taskflow_rag.ticket_store import TicketStore


configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TaskFlow Support Assistant API",
    description="RAG-powered support chatbot and ticket creation API.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ticket_store = TicketStore()


class HealthResponse(BaseModel):
    """Health-check response."""

    status: str


class ChatRequest(BaseModel):
    """Incoming chat question."""

    question: str = Field(..., min_length=1, max_length=1000)


class ChatResponse(BaseModel):
    """RAG answer returned to frontend clients."""

    answer: str
    sources: list[str] = Field(default_factory=list)
    confidence: float
    escalate: bool


class TicketCreateRequest(BaseModel):
    """Support ticket creation payload."""

    question: str = Field(..., min_length=1, max_length=2000)
    user_name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr


class TicketCreateResponse(BaseModel):
    """Ticket creation confirmation."""

    ticket_id: str
    status: str
    message: str


class TicketSummary(BaseModel):
    """Compact ticket list item."""

    ticket_id: str
    status: str


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Return API health status."""

    return HealthResponse(status="healthy")


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Answer a TaskFlow support question using RAG."""

    try:
        payload = answer_question_with_metadata(request.question)
    except FileNotFoundError as exc:
        logger.exception("Chat request failed because ChromaDB is missing: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.exception("Chat request failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected chat error: %s", exc)
        raise HTTPException(status_code=500, detail="Unexpected chat service error.") from exc

    return ChatResponse(**payload)


@app.post("/ticket", response_model=TicketCreateResponse)
def create_ticket(request: TicketCreateRequest) -> TicketCreateResponse:
    """Create a support ticket for questions that need human follow-up."""

    try:
        ticket = ticket_store.create_ticket(
            user_name=request.user_name,
            email=str(request.email),
            question=request.question,
        )
    except RuntimeError as exc:
        logger.exception("Ticket creation failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return TicketCreateResponse(
        ticket_id=ticket["ticket_id"],
        status=ticket["status"],
        message="Ticket created successfully",
    )


@app.get("/tickets", response_model=list[TicketSummary])
def get_tickets() -> list[TicketSummary]:
    """Return compact summaries for all support tickets."""

    try:
        tickets = ticket_store.list_tickets()
    except RuntimeError as exc:
        logger.exception("Unable to list tickets: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return [
        TicketSummary(ticket_id=str(ticket["ticket_id"]), status=str(ticket["status"]))
        for ticket in tickets
    ]
