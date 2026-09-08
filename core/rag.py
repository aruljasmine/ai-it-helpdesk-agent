"""
core/rag.py
------------
Implements Retrieval-Augmented Generation (RAG).

WHAT IS RAG, IN PLAIN ENGLISH?
An LLM only "knows" what it saw during training - it has never read
YOUR company's IT documents. RAG fixes this in five steps:
  1. Split your documents into small chunks.
  2. Convert each chunk into a vector (a list of numbers capturing its
     meaning) - this is called an "embedding".
  3. Store those vectors in a vector database.
  4. At question time, embed the user's question too, and search the
     database for the chunks whose vectors are closest in meaning
     ("semantic search" - it matches meaning, not just keywords).
  5. Hand those chunks to the LLM as extra context, so its answer is
     grounded in real, retrieved facts instead of guesses.

WHY CHROMADB OVER FAISS HERE?
ChromaDB is an embedded vector database (like SQLite, but for
vectors) - no separate server, built-in on-disk persistence, and
built-in metadata storage (we tag every chunk with its category).
FAISS is a lower-level library: it's faster at huge scale (millions
of vectors), but you must build persistence and metadata handling
yourself. For a knowledge base of a few dozen articles, ChromaDB is
the pragmatic choice; the search interface below could be swapped
for a FAISS-backed one without changing any other file, because the
rest of the app only depends on the KnowledgeBase.search() method.
"""

import logging
from pathlib import Path
from typing import List, Dict

import chromadb
from google import genai
from google.genai import types

from config import (
    KNOWLEDGE_BASE_DIR,
    VECTOR_STORE_DIR,
    GEMINI_EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    TOP_K_RESULTS,
)

logger = logging.getLogger(__name__)

COLLECTION_NAME = "it_knowledge_base"


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Splits long text into overlapping chunks.

    WHY OVERLAP? If a sentence explaining "how to fix VPN timeouts" is
    cut exactly in half between two chunks, neither chunk alone makes
    full sense. A small overlap (e.g. 100 characters) repeats the tail
    of one chunk at the start of the next, so no idea is fully lost at
    a chunk boundary.
    """
    text = text.strip()
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end].strip())
        start = end - overlap
    return [c for c in chunks if c]


class KnowledgeBase:
    """
    Wraps embedding + vector storage + retrieval behind one simple API:
    kb.search("my wifi keeps dropping") -> list of relevant text chunks.
    """

    def __init__(self, api_key: str):
        self._client = genai.Client(api_key=api_key)
        self._chroma = chromadb.PersistentClient(path=str(VECTOR_STORE_DIR))
        self._collection = self._chroma.get_or_create_collection(name=COLLECTION_NAME)

    def _embed(self, text: str, task_type: str) -> List[float]:
        """
        Calls Gemini's embedding model. task_type differs for documents
        vs. queries because the embedding model is trained to place a
        *question* and its matching *answer passage* close together in
        vector space only when told which one is which.
        """
        response = self._client.models.embed_content(
            model=GEMINI_EMBEDDING_MODEL,
            contents=text,
            config=types.EmbedContentConfig(task_type=task_type),
        )
        return response.embeddings[0].values

    def is_empty(self) -> bool:
        return self._collection.count() == 0

    def index_documents(self, force: bool = False) -> int:
        """
        Reads every .md file in data/knowledge_base, chunks it, embeds
        each chunk, and stores it in ChromaDB. Skips the work if the
        collection is already populated (unless force=True) so we don't
        re-embed the whole knowledge base on every Streamlit rerun.
        """
        if not force and not self.is_empty():
            logger.info("Knowledge base already indexed (%s chunks). Skipping.", self._collection.count())
            return self._collection.count()

        if force and not self.is_empty():
            self._chroma.delete_collection(COLLECTION_NAME)
            self._collection = self._chroma.get_or_create_collection(name=COLLECTION_NAME)

        md_files = sorted(Path(KNOWLEDGE_BASE_DIR).glob("*.md"))
        if not md_files:
            logger.warning("No knowledge base documents found in %s", KNOWLEDGE_BASE_DIR)
            return 0

        ids, embeddings, documents, metadatas = [], [], [], []
        for file_path in md_files:
            category = file_path.stem  # e.g. "wifi_internet"
            text = file_path.read_text(encoding="utf-8")
            for i, chunk in enumerate(chunk_text(text)):
                ids.append(f"{category}-{i}")
                embeddings.append(self._embed(chunk, task_type="RETRIEVAL_DOCUMENT"))
                documents.append(chunk)
                metadatas.append({"category": category, "source": file_path.name})

        self._collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
        logger.info("Indexed %s chunks from %s documents.", len(ids), len(md_files))
        return len(ids)

    def search(self, query: str, top_k: int = TOP_K_RESULTS) -> List[Dict]:
        """
        Semantic search: returns the top_k chunks most relevant to `query`.
        Each result looks like: {"text": ..., "category": ..., "distance": ...}
        Lower distance means more similar.
        """
        query_embedding = self._embed(query, task_type="RETRIEVAL_QUERY")
        results = self._collection.query(query_embeddings=[query_embedding], n_results=top_k)

        hits = []
        docs = results.get("documents") or [[]]
        metas = results.get("metadatas") or [[]]
        dists = results.get("distances") or [[]]
        for doc, meta, dist in zip(docs[0], metas[0], dists[0]):
            hits.append({"text": doc, "category": meta.get("category", "unknown"), "distance": dist})
        return hits

    def get_full_document(self, category: str) -> str:
        """
        Returns the full, original troubleshooting document for a known
        category (used by the get_troubleshooting_steps tool), instead
        of a possibly-fragmented chunk from semantic search.
        """
        file_path = Path(KNOWLEDGE_BASE_DIR) / f"{category}.md"
        if file_path.exists():
            return file_path.read_text(encoding="utf-8")
        return ""

    def list_categories(self) -> List[str]:
        return sorted(p.stem for p in Path(KNOWLEDGE_BASE_DIR).glob("*.md"))
