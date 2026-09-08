# AI IT Helpdesk Agent

An autonomous IT support chatbot that combines an **AI Agent**, **RAG**
(Retrieval-Augmented Generation), **tool calling**, and **conversation
memory** to diagnose common IT problems and, when needed, raise support
tickets.

## Architecture

```
                         ┌─────────────────────┐
                         │   Streamlit UI       │  app.py
                         │  (chat + sidebar)     │
                         └──────────┬───────────┘
                                    │
                         ┌──────────▼───────────┐
                         │   HelpdeskAgent        │  core/agent.py
                         │  (Gemini + tool loop)  │
                         └──┬────────────────┬───┘
                            │                │
                 ┌──────────▼──────┐   ┌─────▼─────────────┐
                 │  HelpdeskTools    │   │ ConversationMemory │  core/memory.py
                 │ (5 tools)         │   └────────────────────┘
                 └──┬───────────┬───┘
                    │           │
        ┌───────────▼───┐   ┌───▼─────────────┐
        │  KnowledgeBase  │   │  SQLite tickets  │
        │ (RAG: Chroma +  │   │  core/database.py │
        │  Gemini embed)  │   └──────────────────┘
        └─────────────────┘
```

## How the agent decides what to do

Every user message goes through `HelpdeskAgent.handle_message()`:

1. The message (plus a short memory summary) is sent to Gemini along
   with the 5 available tools.
2. Gemini either replies directly, or asks to call one or more tools.
3. Python executes the real tool and sends the result back to Gemini.
4. Gemini produces the final, grounded answer.

This loop is what makes it an **agent** rather than a plain chatbot -
it decides for itself whether to search the knowledge base, fetch a
fixed troubleshooting guide, create a ticket, check a ticket, or
escalate, based on the system prompt and the conversation so far.

## Project structure

```
ai_it_helpdesk/
├── app.py                        # Streamlit UI
├── config.py                     # single source of truth for settings
├── requirements.txt
├── .env.example
├── core/
│   ├── agent.py                  # agent loop (LLM + tool calling)
│   ├── tools.py                  # the 5 tools the agent can call
│   ├── rag.py                    # embeddings + ChromaDB retrieval
│   ├── memory.py                 # conversation memory
│   └── database.py               # SQLite ticket storage
└── data/
    ├── tickets.db                 # auto-created on first run
    └── knowledge_base/
        ├── wifi_internet.md
        ├── password_reset.md
        ├── vpn_issues.md
        ├── printer_issues.md
        ├── software_installation.md
        ├── slow_performance.md
        └── email_login.md
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env        # then paste your Gemini API key into .env
streamlit run app.py
```

You can also skip `.env` entirely and paste the API key directly into
the sidebar when the app opens - it's kept only in the browser session.

Get a free Gemini API key at https://aistudio.google.com/apikey.

## Technology choices and why

| Concern | Choice | Why over the alternative |
|---|---|---|
| LLM | Gemini (`gemini-2.5-flash`) via `google-genai` SDK | Requested by the spec; `google-genai` is Google's current SDK (the older `google-generativeai` package is deprecated) |
| Agent framework | Hand-rolled loop in `core/agent.py` | LangChain would hide the exact tool-calling mechanics a project like this should demonstrate; the hand-rolled loop is ~60 lines and fully explainable in a viva |
| Vector DB | ChromaDB (embedded, persistent) | No server to run, built-in metadata + persistence; FAISS would need that built manually and only pays off at much larger scale |
| Ticket storage | SQLite | Safer than a JSON file under concurrent writes, still zero-config |
| Frontend | Streamlit | Fast to build a real chat UI in pure Python, matches the requested stack |

## Testing suggestions

- **Unit test the tools** in isolation (`core/tools.py`) by injecting a
  fake `KnowledgeBase`, so you don't need API calls to test ticket
  creation logic.
- **Unit test `chunk_text`** for edge cases: empty string, text shorter
  than `chunk_size`, text with no natural break points.
- **Integration test the RAG pipeline**: index the knowledge base, then
  assert that searching "printer offline" returns a chunk tagged
  `category == "printer_issues"`.
- **Manual agent tests**: run each of the 5 example queries and confirm
  the tool badges shown in the UI match what you'd expect (e.g. a
  vague "my computer is slow" should first trigger a clarifying
  question or `search_knowledge_base`, not an immediate ticket).

## Known limitations / suggested improvements

- Ticket IDs are currently extracted from the tool's *text* response
  with `.split()`. For a production system, return structured JSON
  from tools and parse that instead of string-matching.
- There's no authentication - anyone with the URL can create tickets.
  Add login (e.g. via your SSO) before any real deployment.
- The knowledge base is static `.md` files. A production version
  would let IT staff add/edit articles through an admin UI, and
  re-embed automatically on save.
- No automated test suite is included yet - see "Testing suggestions"
  above for where to start.
