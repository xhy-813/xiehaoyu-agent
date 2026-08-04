"""Shared constants for the RAG module.

Separated from ingest.py and retriever.py to avoid circular imports
when running ``python -m rag.ingest``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

COLLECTION = "xhy_kb"
# HuggingFace model ID — sentence-transformers will resolve it from the local
# HF cache (~/.cache/huggingface/hub/).  The model is downloaded once on first use.
EMBED_MODEL = "BAAI/bge-large-zh-v1.5"

# Zhipu AI embedding-3 endpoint (OpenAI-compatible)
ZHIPU_EMBED_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
ZHIPU_EMBED_MODEL = "embedding-3"
# embedding-3 supports 256 / 512 / 1024 / 2048; 1024 balances quality and storage
ZHIPU_EMBED_DIMENSIONS = 1024


def get_embedding_function():
    """Return the appropriate ChromaDB EmbeddingFunction.

    - If ``EMBED_API_KEY`` is set in the environment, uses Zhipu AI
      ``embedding-3`` via the OpenAI-compatible HTTP API (zero local RAM).
    - Otherwise falls back to the local BGE-large model loaded by
      sentence-transformers (~1.3 GB RAM).
    """
    import os

    # .env is loaded by configs.settings at import time — no need to reload
    api_key = os.getenv("EMBED_API_KEY", "")
    if api_key:
        return _ZhipuEmbeddingFunction(
            api_key=api_key,
            base_url=os.getenv("EMBED_API_BASE", ZHIPU_EMBED_BASE_URL),
            model=os.getenv("EMBED_MODEL_NAME", ZHIPU_EMBED_MODEL),
            dimensions=int(os.getenv("EMBED_DIMENSIONS", str(ZHIPU_EMBED_DIMENSIONS))),
        )

    # Local fallback
    from chromadb.utils import embedding_functions

    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL
    )


class _ZhipuEmbeddingFunction:
    """ChromaDB-compatible EmbeddingFunction backed by Zhipu AI embedding-3.

    The Zhipu AI /embeddings endpoint is OpenAI-compatible, so we reuse the
    ``openai`` package that is already a transitive dependency.

    Limitations (per official docs):
      - Single text max 3 072 tokens
      - Batch max 64 texts per request
      - Supported dimensions: 256 / 512 / 1024 / 2048
    """

    # ChromaDB EmbeddingFunction protocol — name() is required by newer versions
    def name(self) -> str:
        return "ZhipuEmbeddingFunction"

    def __init__(
        self,
        api_key: str,
        base_url: str = ZHIPU_EMBED_BASE_URL,
        model: str = ZHIPU_EMBED_MODEL,
        dimensions: int = ZHIPU_EMBED_DIMENSIONS,
    ) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._dimensions = dimensions

    def __call__(self, input: list[str]) -> list[list[float]]:  # noqa: A002
        """Embed a list of texts and return a list of float vectors."""
        return self._embed(input)

    def embed_query(self, input: list[str]) -> list[list[float]]:  # noqa: A002
        """ChromaDB calls this method during collection.query()."""
        return self._embed(input)

    def embed_documents(self, input: list[str]) -> list[list[float]]:  # noqa: A002
        """ChromaDB calls this method during collection.add()."""
        return self._embed(input)

    def _embed(self, input: list[str]) -> list[list[float]]:
        """Batch embed texts, respecting the 64-per-request API limit."""
        results: list[list[float]] = []
        batch_size = 64
        for i in range(0, len(input), batch_size):
            batch = input[i : i + batch_size]
            resp = self._client.embeddings.create(
                model=self._model,
                input=batch,
                dimensions=self._dimensions,
            )
            ordered = sorted(resp.data, key=lambda e: e.index)
            results.extend(e.embedding for e in ordered)
        return results