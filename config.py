"""
config.py
----------
Centralised configuration for the AI IT Helpdesk Agent.

WHY A SEPARATE CONFIG FILE?
Beginners often scatter constants (model names, file paths, API keys)
across many files. That makes the project hard to maintain: change a
model name and you have to hunt through every file. Keeping all
configuration in ONE place is the "Single Source of Truth" principle -
every other module imports FROM here, nothing imports INTO here.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # reads variables from a local .env file, if one exists

BASE_DIR = Path(__file__).resolve().parent

# --- Gemini API ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004")

# --- Storage paths ---
DATA_DIR = BASE_DIR / "data"
KNOWLEDGE_BASE_DIR = DATA_DIR / "knowledge_base"
VECTOR_STORE_DIR = BASE_DIR / "vector_store"
TICKETS_DB_PATH = DATA_DIR / "tickets.db"

# --- RAG settings ---
CHUNK_SIZE = 700          # characters per chunk before it's embedded
CHUNK_OVERLAP = 100       # characters shared between consecutive chunks
TOP_K_RESULTS = 3         # how many chunks to retrieve per search

# --- Agent settings ---
MAX_TOOL_ITERATIONS = 5   # safety limit against infinite tool-call loops
