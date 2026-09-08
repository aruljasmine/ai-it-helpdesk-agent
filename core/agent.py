"""
core/agent.py
--------------
The AI Agent "brain": wires the LLM, the tools, the RAG knowledge base
and conversation memory together into one autonomous IT support agent.

HOW THE AGENT LOOP WORKS, IN PLAIN ENGLISH:
1. We send Gemini the user's message, the conversation history, a
   system prompt describing its job, and the list of tools it is
   allowed to call.
2. Gemini replies with EITHER plain text, OR a request to call one or
   more tools (e.g. "call search_knowledge_base with query='...'").
3. If it requested tools, WE execute the real Python functions and
   send their results back to Gemini as a new turn.
4. Gemini then produces its final answer, now grounded in what the
   tools returned. Steps 2-4 repeat up to MAX_TOOL_ITERATIONS times,
   which is a safety limit against the model looping forever.

This is a hand-rolled agent loop rather than a LangChain AgentExecutor.
For a project this size that is a deliberate trade-off: LangChain saves
you writing this loop, but adds a large dependency surface and hides
exactly the mechanics a final-year project should demonstrate
understanding of. The public shape of HelpdeskAgent.handle_message()
would not need to change if you swapped this implementation for
LangChain / LangGraph later.
"""

import logging
from typing import List, Tuple

from google import genai
from google.genai import types

from config import GEMINI_CHAT_MODEL, MAX_TOOL_ITERATIONS
from core.memory import ConversationMemory
from core.tools import HelpdeskTools, VALID_CATEGORIES

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = f"""You are an autonomous IT Helpdesk Agent for a company's internal staff.

Your job:
- Understand the user's technical problem. Ask ONE short clarifying
  question if the problem is too vague to diagnose (e.g. "my computer
  is slow" with no other detail).
- Use your tools to ground every troubleshooting answer in the real
  knowledge base rather than guessing. Prefer search_knowledge_base for
  an open-ended description, and get_troubleshooting_steps once you are
  confident of the exact category.
- Give clear, numbered, step-by-step instructions a non-technical
  employee can follow.
- If the knowledge-base steps do not resolve the issue, or the user
  says it is still broken after trying them, call create_support_ticket
  and clearly tell the user the ticket ID.
- If the issue is security-sensitive (e.g. possible account compromise)
  or the user is clearly stuck after repeated attempts, call
  escalate_issue instead of a normal ticket.
- If the user asks about an existing ticket, call check_ticket_status.
- Never invent a ticket ID - only report IDs returned by your tools.
- Known issue categories: {', '.join(VALID_CATEGORIES)}.

Keep replies concise and friendly. Use short paragraphs and numbered
steps rather than long blocks of text.
"""


class HelpdeskAgent:
    def __init__(self, api_key: str, tools: HelpdeskTools):
        self._client = genai.Client(api_key=api_key)
        self._tools = tools
        self._chat = self._client.chats.create(
            model=GEMINI_CHAT_MODEL,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=tools.as_list(),
                # We disable the SDK's built-in auto-calling so that WE control
                # execution - this lets us log every tool call and update
                # ConversationMemory as a side effect, which the UI relies on.
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                temperature=0.3,
            ),
        )

    def _execute_tool(self, name: str, args: dict) -> str:
        """Maps a tool name requested by Gemini to the real Python method and runs it."""
        method = getattr(self._tools, name, None)
        if method is None:
            logger.error("Model requested an unknown tool: %s", name)
            return f"Error: tool '{name}' does not exist."
        try:
            return method(**args)
        except Exception as exc:  # a broken tool must never crash the whole app
            logger.exception("Tool '%s' failed with args %s", name, args)
            return f"Error while running tool '{name}': {exc}"

    def _sync_memory_with_tool_call(self, name: str, args: dict, result: str, memory: ConversationMemory) -> None:
        """Keeps ConversationMemory in sync with what the tools actually did."""
        if name == "get_troubleshooting_steps" and "category" in args:
            memory.set_category(args["category"])
        if name in ("create_support_ticket", "escalate_issue"):
            marker = "Ticket ID:" if "Ticket ID:" in result else "Escalated ticket ID:"
            if marker in result:
                ticket_id = result.split(marker)[1].split(".")[0].strip()
                memory.record_ticket(ticket_id)

    def handle_message(self, user_message: str, memory: ConversationMemory) -> Tuple[str, List[str]]:
        """
        Sends one user message through the full agent loop and returns
        (final_reply_text, tools_used) where tools_used is the ordered
        list of tool names the agent invoked - useful for showing the
        user *how* the agent reached its answer.
        """
        memory.add_user_message(user_message)
        tools_used: List[str] = []

        # A short structured reminder, on top of the SDK's own chat history,
        # so the model reliably "remembers" the category and prior ticket.
        contextual_message = f"[Session context: {memory.as_context_summary()}]\n\nUser: {user_message}"

        try:
            response = self._chat.send_message(contextual_message)
        except Exception as exc:
            logger.exception("Gemini call failed")
            reply = ("Sorry, I couldn't reach the AI service just now. Please try "
                     f"again in a moment, or ask me to create a support ticket. (Detail: {exc})")
            memory.add_assistant_message(reply)
            return reply, tools_used

        iterations = 0
        while response.function_calls and iterations < MAX_TOOL_ITERATIONS:
            response_parts = []
            for call in response.function_calls:
                args = dict(call.args) if call.args else {}
                logger.info("Agent calling tool: %s(%s)", call.name, args)
                result = self._execute_tool(call.name, args)
                self._sync_memory_with_tool_call(call.name, args, result, memory)
                tools_used.append(call.name)
                response_parts.append(types.Part.from_function_response(name=call.name, response={"result": result}))

            try:
                response = self._chat.send_message(response_parts)
            except Exception:
                logger.exception("Gemini follow-up call failed")
                reply = "Sorry, something went wrong while processing the tool results. Please try again."
                memory.add_assistant_message(reply)
                return reply, tools_used
            iterations += 1

        final_text = response.text or "I'm sorry, I couldn't generate a response. Could you rephrase your issue?"
        memory.add_assistant_message(final_text)
        return final_text, tools_used
