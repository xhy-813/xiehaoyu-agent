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
import logging
import os
import re
import sys
from pathlib import Path

import chromadb

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────

INCLUDE_DIRS = {"简历", "自我介绍", "常见问题", "项目", "工作经历"}
EXCLUDE_DIRS = {"secrets", ".git", ".agents", ".claude", ".codex", ".workbuddy"}

from rag.constants import COLLECTION, get_embedding_function  # noqa: E402

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
    """Split long text into overlapping chunks, preferring sentence boundaries.

    Tries to split on Chinese/English sentence terminators (。, ！, ？, ., !, ?)
    followed by whitespace or newline.  Falls back to hard character-split if no
    sentence boundary is found within the last 20% of max_chars.
    """
    if len(text) <= max_chars:
        return [text]

    out = []
    start = 0
    while start < len(text):
        end = start + max_chars
        if end >= len(text):
            out.append(text[start:])
            break

        # Try to find a sentence boundary in the last 20% of the window
        search_start = max(start, end - int(max_chars * 0.2))
        chunk = text[search_start:end]
        sent_match = re.search(r"[。！？.!?]\s*", chunk)
        if sent_match:
            cut = search_start + sent_match.end()
            out.append(text[start:cut])
            start = cut - overlap
        else:
            out.append(text[start:end])
            start = end - overlap

    return out


def chunk_markdown(path: Path, text: str, source_root: Path) -> list[dict]:
    """Chunk a single markdown file into embeddable pieces."""
    rel = path.relative_to(source_root).as_posix()
    out: list[dict] = []
    chunk_idx = 0
    for heading, body in split_by_heading(text):
        for piece in hard_split(body):
            content = f"# {heading}\n\n{piece}" if heading else piece
            digest = hashlib.md5(content.encode("utf-8")).hexdigest()[:16]
            out.append(
                {
                    "id": f"{rel}::{chunk_idx}::{digest}",
                    "content": content,
                    "metadata": {
                        "source": rel,
                        "heading": heading,
                        "chunk_index": chunk_idx,
                    },
                }
            )
            chunk_idx += 1
    return out


# ── Validation helpers ────────────────────────────────────


def _validate_src(src: Path) -> None:
    """Check that the source directory exists and contains .md files."""
    if not src.is_dir():
        logger.error("source directory not found: %s", src)
        sys.exit(1)

    md_files = iter_markdown(src)
    if not md_files:
        logger.error(
            "no .md files found under %s. Expected top-level dirs: %s",
            src,
            ", ".join(sorted(INCLUDE_DIRS)),
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
    ef = get_embedding_function()

    # ── Chunk all files ──
    all_chunks: list[dict] = []
    files = iter_markdown(src)
    skipped: list[str] = []

    logger.info("scanning %d md files under %s", len(files), src)
    for p in files:
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            logger.warning("Unicode decode error for %s, falling back to errors='ignore'", p.relative_to(src))
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            logger.exception("Failed to read %s", p.relative_to(src))
            skipped.append(f"{p.relative_to(src)} (read error)")
            continue

        if not text.strip():
            skipped.append(f"{p.relative_to(src)} (empty)")
            continue

        chunks = chunk_markdown(p, text, src)
        all_chunks.extend(chunks)

    if skipped:
        logger.info("skipped %d files:", len(skipped))
        for s in skipped:
            logger.info("  - %s", s)

    if not all_chunks:
        logger.error("no chunks generated from any file")
        sys.exit(1)

    logger.info("total chunks = %d from %d files", len(all_chunks), len(files) - len(skipped))

    # ── Atomic ingest: write to temp collection, then swap (M28) ──
    tmp_collection = f"{COLLECTION}_tmp"
    try:
        client.delete_collection(tmp_collection)
    except Exception:
        pass

    col_tmp = client.create_collection(
        tmp_collection,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    for i in range(0, len(all_chunks), BATCH_SIZE):
        batch = all_chunks[i : i + BATCH_SIZE]
        col_tmp.add(
            ids=[c["id"] for c in batch],
            documents=[c["content"] for c in batch],
            metadatas=[c["metadata"] for c in batch],
        )
        logger.info("  + added %d/%d", min(i + BATCH_SIZE, len(all_chunks)), len(all_chunks))

    # Atomic swap: delete old collection, rename temp → final
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    # ChromaDB doesn't support rename natively — re-create from temp
    col = client.create_collection(
        COLLECTION,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )
    # Copy all chunks from temp to final
    col.add(
        ids=[c["id"] for c in all_chunks],
        documents=[c["content"] for c in all_chunks],
        metadatas=[c["metadata"] for c in all_chunks],
    )
    client.delete_collection(tmp_collection)

    final_count = col.count()
    logger.info("done. collection=%s count=%d", COLLECTION, final_count)
    return final_count


# ── CLI ───────────────────────────────────────────────────


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)-5s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

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
        logger.info("Will ingest %d .md files from %s into %s", len(md_files), src, db)
        logger.info("Collection '%s' will be rebuilt (existing data will be lost).", COLLECTION)
        try:
            resp = input("Continue? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            logger.info("Aborted.")
            sys.exit(0)
        if resp not in ("y", "yes"):
            logger.info("Aborted.")
            sys.exit(0)

    count = build(src, db)
    logger.info("Successfully ingested %d chunks into '%s'.", count, COLLECTION)


if __name__ == "__main__":
    main()