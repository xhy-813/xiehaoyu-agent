"""Ingest personal knowledge-base markdown into a Chroma collection.

用法：
    python -m rag.ingest \\
        --src "data/知识库" \\
        --db  rag/data/chroma

- 扫描以下顶层目录下所有 .md：简历, 自我介绍, 常见问题, 项目, 工作经历
- 显式排除：secrets/、.git/、.agents/、.claude/、.codex/、.workbuddy/
- 按 markdown 标题（H1/H2/H3）切片；单段过长再按 800 字硬切、重叠 80
- 嵌入模型：BAAI/bge-large-zh-v1.5（本地运行，首次运行会下载）
- 存储：Chroma PersistentClient，collection 名 xhy_kb，cosine 距离
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions


# Prevent sentence-transformers from calling HuggingFace Hub
# (model is already cached locally)
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


# ── Constants ─────────────────────────────────────────────

INCLUDE_DIRS = {"简历", "自我介绍", "常见问题", "项目", "工作经历"}
EXCLUDE_DIRS = {"secrets", ".git", ".agents", ".claude", ".codex", ".workbuddy"}

from rag.constants import COLLECTION, EMBED_MODEL  # noqa: E402

MAX_CHARS = 800
OVERLAP = 80
BATCH_SIZE = 200


# ── File discovery ────────────────────────────────────────


def iter_markdown(root: Path) -> list[Path]:
    """Scan root for .md files under allowed top-level directories.

    Returns a sorted list for deterministic ingestion order.
    """
    files: list[Path] = []
    for p in root.rglob("*.md"):
        parts = {x.lower() for x in p.relative_to(root).parts}
        if parts & EXCLUDE_DIRS:
            continue
        top = p.relative_to(root).parts[0].lower() if p.relative_to(root).parts else ""
        if INCLUDE_DIRS and top not in INCLUDE_DIRS:
            continue
        files.append(p)
    return sorted(files)


# ── Chunking ──────────────────────────────────────────────

_HEADING_RE = re.compile(r"^(#{1,3})\s+(.+?)\s*$", re.MULTILINE)


def split_by_heading(text: str) -> list[tuple[str, str]]:
    """Return list of (heading_path, chunk_text). heading_path 形如 'H1 > H2 > H3'."""
    matches = list(_HEADING_RE.finditer(text))
    if not matches:
        body = text.strip()
        return [("", body)] if body else []

    chunks: list[tuple[str, str]] = []
    stack: list[tuple[int, str]] = []  # (level, title)

    # 首段（第一处标题之前的正文）也保留
    if matches[0].start() > 0:
        preface = text[: matches[0].start()].strip()
        if preface:
            chunks.append(("", preface))

    for i, m in enumerate(matches):
        level = len(m.group(1))
        title = m.group(2).strip()
        # 维护标题栈
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, title))
        path = " > ".join(t for _, t in stack)

        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            chunks.append((path, body))
    return chunks


def hard_split(text: str, max_chars: int = MAX_CHARS, overlap: int = OVERLAP) -> list[str]:
    """Split long text into overlapping chunks of at most max_chars."""
    if len(text) <= max_chars:
        return [text]
    out = []
    i = 0
    while i < len(text):
        out.append(text[i : i + max_chars])
        i += max_chars - overlap
    return out


def chunk_markdown(path: Path, text: str, source_root: Path) -> list[dict]:
    """Chunk a single markdown file into embeddable pieces."""
    rel = path.relative_to(source_root).as_posix()
    out: list[dict] = []
    global_idx = 0
    for heading, body in split_by_heading(text):
        for piece in hard_split(body):
            content = f"# {heading}\n\n{piece}" if heading else piece
            digest = hashlib.md5(content.encode("utf-8")).hexdigest()[:16]
            out.append(
                {
                    "id": f"{rel}::{global_idx}::{digest}",
                    "content": content,
                    "metadata": {
                        "source": rel,
                        "heading": heading,
                        "chunk_index": global_idx,
                    },
                }
            )
            global_idx += 1
    return out


# ── Validation helpers ────────────────────────────────────


def _validate_src(src: Path) -> None:
    """Check that the source directory exists and contains .md files."""
    if not src.is_dir():
        print(f"[ingest] ERROR: source directory not found: {src}", file=sys.stderr)
        sys.exit(1)

    md_files = iter_markdown(src)
    if not md_files:
        print(
            f"[ingest] ERROR: no .md files found under {src}. "
            f"Expected top-level dirs: {', '.join(sorted(INCLUDE_DIRS))}",
            file=sys.stderr,
        )
        sys.exit(1)


# ── Build ─────────────────────────────────────────────────


def build(src: Path, db: Path) -> int:
    """Ingest all knowledge-base markdown files into Chroma.

    Returns the number of chunks ingested.
    """
    _validate_src(src)

    db.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(db))
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)

    # 幂等：重建 collection
    try:
        client.delete_collection(COLLECTION)
        print(f"[ingest] dropped existing collection '{COLLECTION}'")
    except Exception:
        pass  # collection didn't exist

    col = client.create_collection(
        COLLECTION,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    # ── Chunk all files ──
    all_chunks: list[dict] = []
    files = iter_markdown(src)
    skipped: list[str] = []

    print(f"[ingest] scanning {len(files)} md files under {src}")
    for p in files:
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            skipped.append(f"{p.relative_to(src)} (read error)")
            continue

        if not text.strip():
            skipped.append(f"{p.relative_to(src)} (empty)")
            continue

        chunks = chunk_markdown(p, text, src)
        all_chunks.extend(chunks)

    if skipped:
        print(f"[ingest] skipped {len(skipped)} files:")
        for s in skipped:
            print(f"  - {s}")

    if not all_chunks:
        print("[ingest] ERROR: no chunks generated from any file.", file=sys.stderr)
        sys.exit(1)

    print(f"[ingest] total chunks = {len(all_chunks)} from {len(files) - len(skipped)} files")

    # ── Batch insert ──
    for i in range(0, len(all_chunks), BATCH_SIZE):
        batch = all_chunks[i : i + BATCH_SIZE]
        col.add(
            ids=[c["id"] for c in batch],
            documents=[c["content"] for c in batch],
            metadatas=[c["metadata"] for c in batch],
        )
        print(f"  + added {min(i + BATCH_SIZE, len(all_chunks))}/{len(all_chunks)}")

    final_count = col.count()
    print(f"[ingest] done. collection={COLLECTION} count={final_count}")
    return final_count


# ── CLI ───────────────────────────────────────────────────


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Ingest personal knowledge-base markdown into ChromaDB.",
    )
    ap.add_argument("--src", default="data/知识库", help="Source directory with .md files")
    ap.add_argument("--db", default="rag/data/chroma", help="ChromaDB persistence directory")
    ap.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation before rebuilding",
    )
    args = ap.parse_args()

    src = Path(args.src)
    db = Path(args.db)

    if not args.force:
        md_files = iter_markdown(src)
        print(f"Will ingest {len(md_files)} .md files from '{src}' into '{db}'")
        print(f"Collection '{COLLECTION}' will be rebuilt (existing data will be lost).")
        try:
            resp = input("Continue? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            sys.exit(0)
        if resp not in ("y", "yes"):
            print("Aborted.")
            sys.exit(0)

    count = build(src, db)
    print(f"\n✓ Successfully ingested {count} chunks into '{COLLECTION}'.")


if __name__ == "__main__":
    main()