"""
app.py
-------
Streamlit front-end for the AI IT Helpdesk Agent.

Run with:
    streamlit run app.py
"""

import logging
import streamlit as st

from config import GEMINI_API_KEY, GEMINI_CHAT_MODEL
from core import database
from core.rag import KnowledgeBase
from core.tools import HelpdeskTools
from core.agent import HelpdeskAgent
from core.memory import ConversationMemory

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("app")

st.set_page_config(page_title="AI IT Helpdesk Agent", page_icon="🛠️", layout="wide")

# ---------------------------------------------------------------------------
# Styling - kept to plain, framework-stable CSS (page background, cards,
# buttons, badges). We intentionally do NOT hack Streamlit's internal chat
# bubble DOM classes, since those change between versions; st.chat_message
# is used as-is for that reason.
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(180deg, #f7f9fc 0%, #eef1f8 100%); }
    .hd-banner {
        background: linear-gradient(120deg, #4338ca 0%, #6d28d9 60%, #7c3aed 100%);
        padding: 1.4rem 1.8rem; border-radius: 16px; color: white; margin-bottom: 1.2rem;
        box-shadow: 0 8px 24px rgba(76, 29, 149, 0.25);
    }
    .hd-banner h1 { margin: 0; font-size: 1.6rem; }
    .hd-banner p { margin: 0.3rem 0 0 0; opacity: 0.9; font-size: 0.92rem; }
    .hd-card {
        background: white; border-radius: 12px; padding: 0.9rem 1rem;
        border: 1px solid #e5e7eb; margin-bottom: 0.8rem;
    }
    .hd-badge {
        display: inline-block; background: #ede9fe; color: #5b21b6;
        font-size: 0.72rem; font-weight: 600; padding: 2px 9px;
        border-radius: 999px; margin-right: 6px; margin-top: 6px;
    }
    .hd-ticket {
        background: #ecfdf5; border: 1px solid #a7f3d0; color: #065f46;
        padding: 0.6rem 0.9rem; border-radius: 10px; font-weight: 600; margin-top: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hd-banner">
        <h1>🛠️ AI IT Helpdesk Agent</h1>
        <p>Autonomous troubleshooting powered by an AI Agent + RAG knowledge base + tool calling</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session bootstrap
# ---------------------------------------------------------------------------
if "api_key" not in st.session_state:
    st.session_state.api_key = GEMINI_API_KEY

with st.sidebar:
    st.subheader("⚙️ Setup")
    api_key_input = st.text_input(
        "Gemini API Key",
        value=st.session_state.api_key,
        type="password",
        help="Get a free key at https://aistudio.google.com/apikey. "
             "You can also set GEMINI_API_KEY in a .env file instead of pasting it here.",
    )
    if api_key_input != st.session_state.api_key:
        st.session_state.api_key = api_key_input
        for key in ("agent", "kb", "memory"):
            st.session_state.pop(key, None)

    st.caption(f"Chat model: `{GEMINI_CHAT_MODEL}`")

if not st.session_state.api_key:
    st.info("👈 Enter your Gemini API key in the sidebar to start chatting with the helpdesk agent.")
    st.stop()

database.init_db()

if "kb" not in st.session_state:
    with st.spinner("Indexing IT knowledge base (first run only)..."):
        kb = KnowledgeBase(api_key=st.session_state.api_key)
        try:
            chunk_count = kb.index_documents()
        except Exception as exc:
            st.error(f"Failed to index the knowledge base: {exc}")
            st.stop()
        st.session_state.kb = kb
        st.session_state.kb_chunk_count = chunk_count

if "memory" not in st.session_state:
    st.session_state.memory = ConversationMemory()

if "agent" not in st.session_state:
    try:
        tools = HelpdeskTools(knowledge_base=st.session_state.kb)
        st.session_state.agent = HelpdeskAgent(api_key=st.session_state.api_key, tools=tools)
    except Exception as exc:
        st.error(f"Failed to initialise the AI agent: {exc}")
        st.stop()

if "chat_display" not in st.session_state:
    st.session_state.chat_display = []  # list of {"role", "content", "tools_used"}

# ---------------------------------------------------------------------------
# Sidebar: knowledge base status, ticket lookup, recent tickets
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("---")
    st.subheader("📚 Knowledge Base")
    st.caption(f"{st.session_state.get('kb_chunk_count', st.session_state.kb._collection.count())} chunks indexed "
               f"across {len(st.session_state.kb.list_categories())} categories.")
    if st.button("🔄 Re-index knowledge base", use_container_width=True):
        with st.spinner("Re-indexing..."):
            count = st.session_state.kb.index_documents(force=True)
            st.session_state.kb_chunk_count = count
        st.success(f"Re-indexed {count} chunks.")

    st.markdown("---")
    st.subheader("🎫 Check a Ticket")
    lookup_id = st.text_input("Ticket ID", placeholder="TCK-4F9A2B")
    if st.button("Check status", use_container_width=True) and lookup_id:
        ticket = database.get_ticket(lookup_id.strip().upper())
        if ticket:
            st.markdown(
                f"<div class='hd-ticket'>Status: {ticket['status'].upper()}<br>"
                f"Priority: {ticket['priority']} &nbsp;|&nbsp; Category: {ticket['category']}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.warning("Ticket not found.")

    st.markdown("---")
    st.subheader("🗂️ Recent Tickets")
    recent = database.list_tickets(limit=5)
    if not recent:
        st.caption("No tickets created yet.")
    else:
        for t in recent:
            st.markdown(
                f"<div class='hd-card'><b>{t['ticket_id']}</b> · {t['status']}<br>"
                f"<span style='font-size:0.8rem;color:#666'>{t['category']} · {t['priority']}</span></div>",
                unsafe_allow_html=True,
            )

    if st.button("🧹 Reset conversation", use_container_width=True):
        st.session_state.memory = ConversationMemory()
        st.session_state.chat_display = []
        st.rerun()

# ---------------------------------------------------------------------------
# Quick-start example queries
# ---------------------------------------------------------------------------
st.caption("Try an example, or describe your own IT problem below:")
examples = [
    "My Wi-Fi is connected but internet is not working.",
    "I forgot my company account password.",
    "My VPN is not connecting.",
    "My laptop is very slow.",
    "I cannot print documents.",
]
cols = st.columns(len(examples))
pending_prompt = None
for col, example in zip(cols, examples):
    if col.button(example, use_container_width=True):
        pending_prompt = example

# ---------------------------------------------------------------------------
# Chat history render
# ---------------------------------------------------------------------------
for turn in st.session_state.chat_display:
    avatar = "🧑‍💻" if turn["role"] == "user" else "🤖"
    with st.chat_message(turn["role"], avatar=avatar):
        st.markdown(turn["content"])
        if turn.get("tools_used"):
            badges = "".join(f"<span class='hd-badge'>🔧 {t}</span>" for t in turn["tools_used"])
            st.markdown(badges, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Chat input + agent turn
# ---------------------------------------------------------------------------
user_input = st.chat_input("Describe your IT problem...")
final_input = pending_prompt or user_input

if final_input:
    st.session_state.chat_display.append({"role": "user", "content": final_input})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(final_input)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking..."):
            try:
                reply, tools_used = st.session_state.agent.handle_message(final_input, st.session_state.memory)
            except Exception as exc:
                logger.exception("Unhandled agent error")
                reply, tools_used = (
                    "Something went wrong on my end. Please try again, or ask me to create a support ticket.",
                    [],
                )
        st.markdown(reply)
        if tools_used:
            badges = "".join(f"<span class='hd-badge'>🔧 {t}</span>" for t in tools_used)
            st.markdown(badges, unsafe_allow_html=True)

    st.session_state.chat_display.append({"role": "assistant", "content": reply, "tools_used": tools_used})
