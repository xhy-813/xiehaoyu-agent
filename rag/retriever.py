"""Top-k retriever over the personal-knowledge Chroma collection."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

from rag.ingest import COLLECTION, EMBED_MODEL


DEFAULT_DB = Path(__file__).resolve().parents[1] / "rag" / "data" / "chroma"


@dataclass
class Hit:
    content: str
    source: str
    heading: str
    score: float  # cosine distance；越小越相关


@lru_cache(maxsize=1)
def _collection(db_path: str):
    client = chromadb.PersistentClient(path=db_path)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
    return client.get_collection(COLLECTION, embedding_function=ef)


def retrieve(question: str, top_k: int = 5, db_path: Path | None = None) -> list[Hit]:
    col = _collection(str(db_path or DEFAULT_DB))
    res = col.query(query_texts=[question], n_results=top_k)
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    dists = res.get("distances", [[]])[0]
    return [
        Hit(
            content=d,
            source=m.get("source", ""),
            heading=m.get("heading", ""),
            score=float(s),
        )
        for d, m, s in zip(docs, metas, dists)
    ]
