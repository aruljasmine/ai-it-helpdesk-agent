"""
core/tools.py
--------------
The concrete "tools" the AI agent is allowed to call.

WHAT IS "TOOL CALLING", IN PLAIN ENGLISH?
An LLM can only generate text - it cannot, by itself, query a
database or create a ticket. Tool calling lets us describe a set of
Python functions (name, parameters, purpose) to the model. When the
model decides a function would help, it replies with a structured
request such as "call get_troubleshooting_steps with
category='wifi_internet'" instead of plain text. Our code then runs
the REAL Python function and feeds the result back to the model. This
is what turns a chatbot into an "agent" - it can act, not just talk.

Each method below is deliberately simple, type-hinted, and documented
with a Google-style docstring, because the Gemini SDK reads the
Python signature and docstring to automatically build the tool's
schema - there is no separate JSON schema to maintain by hand.
"""

import logging
from typing import List

from core.rag import KnowledgeBase
from core import database

logger = logging.getLogger(__name__)

VALID_CATEGORIES = [
    "wifi_internet",
    "password_reset",
    "vpn_issues",
    "printer_issues",
    "software_installation",
    "slow_performance",
    "email_login",
]


class HelpdeskTools:
    """Bundles all agent tools together with the shared KnowledgeBase they read from."""

    def __init__(self, knowledge_base: KnowledgeBase):
        self.kb = knowledge_base

    # ---- Tool 1: RAG search --------------------------------------------------
    def search_knowledge_base(self, query: str) -> str:
        """Searches the IT knowledge base for information relevant to a free-text
        description of a problem. Use this first for almost any technical question,
        especially when you are not yet sure which category the issue belongs to.

        Args:
            query: The user's problem, in their own words, e.g. "wifi connects but no internet".
        """
        hits = self.kb.search(query, top_k=3)
        if not hits:
            return "No relevant knowledge base articles were found for that query."
        formatted = "\n\n".join(f"[Category: {h['category']}]\n{h['text']}" for h in hits)
        logger.info("KB search for %r returned %s hit(s)", query, len(hits))
        return formatted

    # ---- Tool 2: deterministic lookup -----------------------------------------
    def get_troubleshooting_steps(self, category: str) -> str:
        """Returns the full, official, ordered troubleshooting guide for ONE known
        issue category. Use this once you are confident which category the user's
        issue belongs to, instead of a broad search.

        Args:
            category: One of wifi_internet, password_reset, vpn_issues, printer_issues,
                software_installation, slow_performance, email_login.
        """
        if category not in VALID_CATEGORIES:
            return (f"'{category}' is not a recognised category. "
                    f"Valid categories are: {', '.join(VALID_CATEGORIES)}.")
        doc = self.kb.get_full_document(category)
        if not doc:
            return f"No troubleshooting guide is stored for '{category}'."
        return doc

    # ---- Tool 3: create ticket -------------------------------------------------
    def create_support_ticket(self, category: str, issue_summary: str, priority: str = "normal") -> str:
        """Creates a new IT support ticket when the user's issue could NOT be
        resolved through troubleshooting. Only call this after relevant
        troubleshooting steps have already been tried, or the user explicitly
        asks for a ticket to be raised.

        Args:
            category: The issue category, e.g. wifi_internet, vpn_issues, printer_issues.
            issue_summary: A one or two sentence summary of the problem and what was already tried.
            priority: One of low, normal, high, critical. Defaults to normal.
        """
        ticket = database.create_ticket(category=category, issue_summary=issue_summary, priority=priority)
        logger.info("Ticket created via tool call: %s", ticket["ticket_id"])
        return (f"Ticket created successfully. Ticket ID: {ticket['ticket_id']}. "
                f"Status: {ticket['status']}. Priority: {ticket['priority']}.")

    # ---- Tool 4: check status ---------------------------------------------------
    def check_ticket_status(self, ticket_id: str) -> str:
        """Looks up the current status of a previously created support ticket.

        Args:
            ticket_id: The ticket ID to look up, e.g. 'TCK-4F9A2B'.
        """
        ticket = database.get_ticket(ticket_id.strip().upper())
        if not ticket:
            return f"No ticket found with ID '{ticket_id}'. Please double-check the ID."
        return (f"Ticket {ticket['ticket_id']}: status={ticket['status']}, "
                f"priority={ticket['priority']}, category={ticket['category']}, "
                f"created_at={ticket['created_at']}.")

    # ---- Tool 5: escalate --------------------------------------------------------
    def escalate_issue(self, category: str, issue_summary: str, reason: str) -> str:
        """Escalates an issue directly to human IT staff as a high-priority ticket.
        Use this for anything security-sensitive (e.g. suspected account compromise),
        business-critical outages, or when the user is clearly stuck after multiple
        failed troubleshooting attempts.

        Args:
            category: The issue category.
            issue_summary: What the problem is and what has already been tried.
            reason: Why this needs human escalation rather than a normal ticket.
        """
        ticket = database.create_ticket(
            category=category,
            issue_summary=f"{issue_summary} | Escalation reason: {reason}",
            priority="high",
            escalated=True,
        )
        logger.warning("Issue escalated: ticket %s (%s)", ticket["ticket_id"], reason)
        return (f"This issue has been escalated to human IT support. "
                f"Escalated ticket ID: {ticket['ticket_id']}. A specialist will contact you.")

    def as_list(self) -> List:
        """Returns the bound tool methods as a list, ready to hand to the Gemini SDK."""
        return [
            self.search_knowledge_base,
            self.get_troubleshooting_steps,
            self.create_support_ticket,
            self.check_ticket_status,
            self.escalate_issue,
        ]
