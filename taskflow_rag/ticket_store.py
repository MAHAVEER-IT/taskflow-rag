"""JSON-backed ticket storage for support escalations."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from taskflow_rag.config import project_dir


TICKET_STATUS_OPEN = "OPEN"


class TicketStore:
    """Small JSON-file ticket store suitable for local development and demos."""

    def __init__(self, storage_path: Path | None = None) -> None:
        self.storage_path = storage_path or project_dir() / "tickets" / "tickets.json"
        self._lock = threading.Lock()
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self._write_tickets([])

    def list_tickets(self) -> list[dict[str, Any]]:
        """Return all stored tickets."""

        with self._lock:
            return self._read_tickets()

    def create_ticket(self, user_name: str, email: str, question: str) -> dict[str, Any]:
        """Create and persist a new support ticket."""

        with self._lock:
            tickets = self._read_tickets()
            ticket = {
                "ticket_id": self._next_ticket_id(tickets),
                "user_name": user_name,
                "email": email,
                "question": question,
                "status": TICKET_STATUS_OPEN,
                "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            }
            tickets.append(ticket)
            self._write_tickets(tickets)
            return ticket

    def _read_tickets(self) -> list[dict[str, Any]]:
        """Read tickets from disk with defensive handling for empty files."""

        try:
            raw_text = self.storage_path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise RuntimeError(f"Unable to read ticket store: {self.storage_path}") from exc

        if not raw_text:
            return []

        try:
            loaded = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Ticket store is not valid JSON: {self.storage_path}") from exc

        if not isinstance(loaded, list):
            raise RuntimeError("Ticket store must contain a JSON list.")

        return loaded

    def _write_tickets(self, tickets: list[dict[str, Any]]) -> None:
        """Write tickets to disk using formatted JSON."""

        try:
            self.storage_path.write_text(
                json.dumps(tickets, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:
            raise RuntimeError(f"Unable to write ticket store: {self.storage_path}") from exc

    def _next_ticket_id(self, tickets: list[dict[str, Any]]) -> str:
        """Generate the next TKT-0001 style ticket ID."""

        highest_number = 0
        for ticket in tickets:
            ticket_id = str(ticket.get("ticket_id", ""))
            if not ticket_id.startswith("TKT-"):
                continue
            try:
                highest_number = max(highest_number, int(ticket_id.removeprefix("TKT-")))
            except ValueError:
                continue

        return f"TKT-{highest_number + 1:04d}"
