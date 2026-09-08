"""
core/memory.py
----------------
Short-term conversation memory for a single chat session.

WHY A SEPARATE CLASS INSTEAD OF JUST USING STREAMLIT'S session_state?
session_state is UI-framework-specific storage. By wrapping memory in
a plain Python class, the Agent's logic doesn't need to know anything
about Streamlit - the same Agent could be reused inside a FastAPI
backend, a CLI tool, or a Slack bot without changing a line of agent
code. This is the "Dependency Inversion" idea from SOLID: the agent
depends on a simple memory interface, not on a specific framework.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Message:
    role: str          # "user" or "assistant"
    content: str


@dataclass
class ConversationMemory:
    """
    Tracks the running chat transcript plus a small amount of
    structured state about the CURRENT issue, so the agent can answer
    things like "did you already tell me to restart the router?"
    reliably, instead of hoping the LLM re-reads the whole transcript.
    """
    messages: List[Message] = field(default_factory=list)
    current_category: Optional[str] = None
    steps_already_suggested: List[str] = field(default_factory=list)
    last_ticket_id: Optional[str] = None

    def add_user_message(self, content: str) -> None:
        self.messages.append(Message(role="user", content=content))

    def add_assistant_message(self, content: str) -> None:
        self.messages.append(Message(role="assistant", content=content))

    def set_category(self, category: str) -> None:
        self.current_category = category

    def record_steps(self, steps: List[str]) -> None:
        self.steps_already_suggested.extend(
            s for s in steps if s not in self.steps_already_suggested
        )

    def record_ticket(self, ticket_id: str) -> None:
        self.last_ticket_id = ticket_id

    def as_context_summary(self) -> str:
        """
        A short text summary the agent can use so Gemini "remembers" the
        issue category and prior ticket, reinforcing the SDK's own chat
        history with an explicit structured reminder.
        """
        parts = []
        if self.current_category:
            parts.append(f"Current issue category: {self.current_category}.")
        if self.steps_already_suggested:
            parts.append("Steps already suggested: " + "; ".join(self.steps_already_suggested))
        if self.last_ticket_id:
            parts.append(f"Most recently created ticket: {self.last_ticket_id}.")
        return " ".join(parts) if parts else "No prior context yet."
