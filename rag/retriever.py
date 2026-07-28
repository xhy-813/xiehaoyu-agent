"""Top-k retriever over the personal-knowledge Chroma collection.

Usage::

    from rag.retriever import retrieve, count, invalidate_cache
    hits = retrieve("介绍一下你自己", top_k=5)
    for h in hits:
        print(f"{h.source} (similarity={h.similarity:.3f}): {h.content[:80]}...")
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

from rag.constants import COLLECTION, EMBED_MODEL


# Prevent sentence-transformers from checking HuggingFace for config files
# (model is already cached locally, no need to ping HF on every load)
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


# Resolved relative to this file for CWD independence
_RETRIEVER_DIR = Path(__file__).resolve().parent
DEFAULT_DB = _RETRIEVER_DIR / "data" / "chroma"


@dataclass
class Hit:
    """A single retrieval result.

    Attributes:
        content: The chunk text.
        source: Relative path of the source file (e.g. ``简历/谢浩宇-简历.md``).
        heading: Breadcrumb heading path (e.g. ``教育背景 > 荣誉``), or ``""``.
        distance: Cosine distance (0–2, lower = more relevant).
        similarity: Cosine similarity (1 – distance, 0–1, higher = more relevant).
    """

    content: str
    source: str
    heading: str
    distance: float  # cosine distance, 越小越相关
    similarity: float = field(init=False)  # 1 – distance, 越大越相关

    def __post_init__(self) -> None:
        self.similarity = round(1.0 - self.distance, 4)


# ── Collection (lazy, cached) ─────────────────────────────

_cached_db_path: str | None = None


@lru_cache(maxsize=1)
def _get_collection(db_path: str):
    """Lazy-load and cache the Chroma collection.

    Cached per *db_path* — calling ``invalidate_cache()`` clears it.
    """
    client = chromadb.PersistentClient(path=db_path)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
    return client.get_collection(COLLECTION, embedding_function=ef)


def invalidate_cache() -> None:
    """Clear the cached collection handle.

    Call this after re-ingesting (``rag.ingest.build()``) so the retriever
    picks up the new collection on the next query.
    """
    _get_collection.cache_clear()


def count(db_path: Path | None = None) -> int:
    """Return the number of chunks in the collection."""
    db = str(db_path or DEFAULT_DB)
    try:
        col = _get_collection(db)
        return col.count()
    except Exception:
        return 0


# ── Retrieve ──────────────────────────────────────────────


def retrieve(question: str, top_k: int = 5, db_path: Path | None = None) -> list[Hit]:
    """Retrieve top-k chunks from the personal knowledge base.

    Args:
        question: Natural-language query (will be embedded with BGE-large-zh-v1.5).
        top_k: Number of chunks to return.
        db_path: Path to ChromaDB persistence directory.  Defaults to
            ``rag/data/chroma/`` relative to the project root.

    Returns:
        List of ``Hit``, ordered by relevance (best first).  Returns an empty
        list if the collection is empty or missing.
    """
    db = str(db_path or DEFAULT_DB)

    try:
        col = _get_collection(db)
    except Exception:
        # Collection doesn't exist or is corrupted — return empty
        return []

    try:
        res = col.query(query_texts=[question], n_results=top_k)
    except Exception:
        return []

    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    dists = res.get("distances", [[]])[0]

    return [
        Hit(
            content=d,
            source=m.get("source", ""),
            heading=m.get("heading", ""),
            distance=float(s),
        )
        for d, m, s in zip(docs, metas, dists)
    ]