"""Shared constants for the RAG module.

Separated from ingest.py and retriever.py to avoid circular imports
when running ``python -m rag.ingest``.
"""

COLLECTION = "xhy_kb"
# HuggingFace model ID — sentence-transformers will resolve it from the local
# HF cache (~/.cache/huggingface/hub/).  The model is downloaded once on first use.
EMBED_MODEL = "BAAI/bge-large-zh-v1.5"