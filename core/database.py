"""
core/database.py
------------------
Handles all persistent storage of IT support tickets using SQLite.

WHY SQLite INSTEAD OF A JSON FILE?
A JSON file has to be fully loaded and rewritten for every change,
which is slow and risks data corruption if two requests write at the
same time. SQLite is a real relational database that ships with
Python, handles concurrent-safe writes, and lets us query tickets
(e.g. "give me ticket TCK-A1B2C3") efficiently instead of scanning a
whole file.
"""

import sqlite3
import logging
import uuid
from datetime import datetime, timezone
from contextlib import contextmanager
from typing import Optional, List, Dict

from config import TICKETS_DB_PATH

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id        TEXT PRIMARY KEY,
    created_at        TEXT NOT NULL,
    category          TEXT NOT NULL,
    issue_summary     TEXT NOT NULL,
    priority          TEXT NOT NULL DEFAULT 'normal',
    status            TEXT NOT NULL DEFAULT 'open',
    escalated         INTEGER NOT NULL DEFAULT 0,
    resolution_notes  TEXT
);
"""


@contextmanager
def get_connection():
    """
    Opens a SQLite connection and guarantees it is closed afterwards,
    even if an error happens. This context-manager pattern avoids the
    classic bug of "forgot to close the connection -> database file
    stays locked for the next request".
    """
    TICKETS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(TICKETS_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Database operation failed; rolled back.")
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Creates the tickets table if it doesn't exist yet. Safe to call on every startup."""
    with get_connection() as conn:
        conn.execute(_SCHEMA)
    logger.info("Ticket database ready at %s", TICKETS_DB_PATH)


def generate_ticket_id() -> str:
    """Generates a short, human-readable, unique ticket ID, e.g. 'TCK-4F9A2B'."""
    return f"TCK-{uuid.uuid4().hex[:6].upper()}"


def create_ticket(category: str, issue_summary: str, priority: str = "normal", escalated: bool = False) -> Dict:
    """
    Inserts a new ticket row and returns it as a dictionary.
    priority is expected to be one of: low, normal, high, critical.
    """
    ticket_id = generate_ticket_id()
    created_at = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO tickets
               (ticket_id, created_at, category, issue_summary, priority, status, escalated)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (ticket_id, created_at, category, issue_summary, priority, "open", int(escalated)),
        )
    logger.info("Created ticket %s (category=%s, priority=%s, escalated=%s)",
                ticket_id, category, priority, escalated)
    return get_ticket(ticket_id)


def get_ticket(ticket_id: str) -> Optional[Dict]:
    """Fetches a single ticket by ID. Returns None if it doesn't exist."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,)).fetchone()
    return dict(row) if row else None


def update_ticket_status(ticket_id: str, status: str, resolution_notes: Optional[str] = None) -> Optional[Dict]:
    """Updates a ticket's status (e.g. to 'resolved' or 'in_progress')."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE tickets SET status = ?, resolution_notes = COALESCE(?, resolution_notes) WHERE ticket_id = ?",
            (status, resolution_notes, ticket_id),
        )
    return get_ticket(ticket_id)


def list_tickets(limit: int = 50) -> List[Dict]:
    """Returns the most recent tickets, newest first. Used by the sidebar ticket viewer."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM tickets ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]
