"""Top-k retriever over the personal-knowledge Chroma collection.

Usage::

    from rag.retriever import retrieve, count, invalidate_cache
    hits = retrieve("介绍一下你自己", top_k=5)
    for h in hits:
        print(f"{h.source} (similarity={h.similarity:.3f}): {h.content[:80]}...")
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import chromadb

from rag.constants import COLLECTION, get_embedding_function

logger = logging.getLogger(__name__)

# Prevent sentence-transformers from checking HuggingFace for config files
# (model is already cached locally, no need to ping HF on every load)
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


# Resolved relative to this file for CWD independence
_RETRIEVER_DIR = Path(__file__).resolve().parent
DEFAULT_DB = _RETRIEVER_DIR / "data" / "chroma"

# Default minimum cosine similarity for retrieval (0.3 = distance ≤ 0.7)
DEFAULT_MIN_SIMILARITY = 0.3


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


@lru_cache(maxsize=1)
def _get_collection(db_path: str):
    """Lazy-load and cache the Chroma collection.

    Cached per *db_path* — calling ``invalidate_cache()`` clears it.
    """
    client = chromadb.PersistentClient(path=db_path)
    ef = get_embedding_function()
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
        logger.exception("Failed to count collection at %s", db)
        return 0


# ── Retrieve ──────────────────────────────────────────────


def retrieve(
    question: str,
    top_k: int = 5,
    db_path: Path | None = None,
    min_similarity: float = DEFAULT_MIN_SIMILARITY,
) -> list[Hit]:
    """Retrieve top-k chunks from the personal knowledge base.

    Args:
        question: Natural-language query (will be embedded with BGE-large-zh-v1.5).
        top_k: Number of chunks to return.
        db_path: Path to ChromaDB persistence directory.  Defaults to
            ``rag/data/chroma/`` relative to the project root.
        min_similarity: Minimum cosine similarity (0–1) to include a result.
            Results below this threshold are filtered out.  Default: 0.3.

    Returns:
        List of ``Hit``, ordered by relevance (best first).  Returns an empty
        list if the collection is empty or missing.
    """
    db = str(db_path or DEFAULT_DB)

    try:
        col = _get_collection(db)
    except Exception:
        logger.exception("Failed to get Chroma collection at %s", db)
        return []

    try:
        res = col.query(query_texts=[question], n_results=top_k)
    except Exception:
        logger.exception("Chroma query failed for: %s", question[:200])
        return []

    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    dists = res.get("distances", [[]])[0]

    hits = []
    low_quality = 0
    for d, m, s in zip(docs, metas, dists):
        sim = round(1.0 - float(s), 4)
        if sim < min_similarity:
            low_quality += 1
            continue
        hits.append(
            Hit(
                content=d,
                source=m.get("source", ""),
                heading=m.get("heading", ""),
                distance=float(s),
            )
        )

    if low_quality > 0:
        logger.info(
            "Filtered %d/%d chunks below similarity threshold %.2f",
            low_quality,
            low_quality + len(hits),
            min_similarity,
        )

    return hits