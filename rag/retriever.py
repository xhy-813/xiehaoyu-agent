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
from chromadb.errors import NotFoundError

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


@dataclass
class RetrievalResult:
    """检索结果 + 健康标志（808 审查 M9）。

    ``degraded=True`` 表示检索基础设施故障（Chroma 损坏、embedding API 异常等），
    与"正常检索但无匹配"（degraded=False, hits=[]）区分开——前者应让 LLM
    诚实说明不可用，而不是凭人设硬答。
    """

    hits: list[Hit]
    degraded: bool = False


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


def retrieve_result(
    question: str,
    top_k: int = 5,
    db_path: Path | None = None,
    min_similarity: float = DEFAULT_MIN_SIMILARITY,
) -> RetrievalResult:
    """Retrieve top-k chunks, with an explicit degradation flag (808 审查 M9).

    Same retrieval logic as ``retrieve()``, but infrastructure failures
    (collection missing, Chroma error, embedding API down) return
    ``RetrievalResult(hits=[], degraded=True)`` instead of a bare empty list.
    """
    db = str(db_path or DEFAULT_DB)

    try:
        col = _get_collection(db)
    except Exception:
        logger.exception("Failed to get Chroma collection at %s", db)
        return RetrievalResult([], degraded=True)

    try:
        res = col.query(query_texts=[question], n_results=top_k)
    except NotFoundError:
        # ingest 在其它进程重建集合后，缓存句柄指向已删除的 UUID：
        # 清缓存按名字重取新集合，重试一次；仍失败则按原逻辑降级返回空
        logger.warning("Cached collection handle is stale (collection rebuilt?), refreshing and retrying once")
        invalidate_cache()
        try:
            res = _get_collection(db).query(query_texts=[question], n_results=top_k)
        except Exception:
            logger.exception("Chroma query failed for: %s", question[:200])
            return RetrievalResult([], degraded=True)
    except Exception:
        logger.exception("Chroma query failed for: %s", question[:200])
        return RetrievalResult([], degraded=True)

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

    return RetrievalResult(hits, degraded=False)


def retrieve(
    question: str,
    top_k: int = 5,
    db_path: Path | None = None,
    min_similarity: float = DEFAULT_MIN_SIMILARITY,
) -> list[Hit]:
    """Retrieve top-k chunks from the personal knowledge base.

    兼容包装：只返回命中列表（丢弃 degraded 标志）。新调用方请使用
    ``retrieve_result()`` 以区分"基础设施故障"与"无匹配"。
    """
    return retrieve_result(
        question, top_k=top_k, db_path=db_path, min_similarity=min_similarity
    ).hits