from rag.constants import COLLECTION, EMBED_MODEL

__all__ = [
    "COLLECTION",
    "EMBED_MODEL",
    "Hit",
    "DEFAULT_DB",
    "build",
    "count",
    "invalidate_cache",
    "retrieve",
]


def __getattr__(name: str):
    """Lazy imports to avoid circular imports when running ``python -m rag.ingest``."""
    if name == "build":
        from rag.ingest import build

        return build
    if name in ("Hit", "DEFAULT_DB", "retrieve", "count", "invalidate_cache"):
        import rag.retriever as _retriever

        return getattr(_retriever, name)
    raise AttributeError(f"module 'rag' has no attribute {name!r}")