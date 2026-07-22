"""Ingest personal knowledge-base markdown into a Chroma collection.

用法：
    python -m rag.ingest \\
        --src "Xiehaoyu-Agent/个人知识库" \\
        --db  rag/data/chroma

- 扫描以下顶层目录下所有 .md（大小写不敏感）：career, school, work, projects, tech, life, methods, templates
- 显式排除：secrets/、.git/、.agents/、.claude/、.codex/、.workbuddy/
- 按 markdown 标题（H1/H2/H3）切片；单段过长再按 800 字硬切、重叠 80
- 嵌入模型：BAAI/bge-small-zh-v1.5（本地跑，首次运行会下载）
- 存储：Chroma PersistentClient，collection 名 xhy_kb
"""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path
from typing import Iterable

import chromadb
from chromadb.utils import embedding_functions


INCLUDE_DIRS = {"career", "school", "work", "projects", "tech", "life", "methods", "templates"}
EXCLUDE_DIRS = {"secrets", ".git", ".agents", ".claude", ".codex", ".workbuddy"}

COLLECTION = "xhy_kb"
EMBED_MODEL = "BAAI/bge-small-zh-v1.5"

MAX_CHARS = 800
OVERLAP = 80


def iter_markdown(root: Path) -> Iterable[Path]:
    for p in root.rglob("*.md"):
        parts = {x.lower() for x in p.relative_to(root).parts}
        if parts & EXCLUDE_DIRS:
            continue
        top = p.relative_to(root).parts[0].lower() if p.relative_to(root).parts else ""
        if INCLUDE_DIRS and top not in INCLUDE_DIRS:
            continue
        yield p


_HEADING_RE = re.compile(r"^(#{1,3})\s+(.+?)\s*$", re.MULTILINE)


def split_by_heading(text: str) -> list[tuple[str, str]]:
    """Return list of (heading_path, chunk_text). heading_path 形如 'H1 > H2 > H3'."""
    matches = list(_HEADING_RE.finditer(text))
    if not matches:
        return [("", text.strip())]

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
    if len(text) <= max_chars:
        return [text]
    out = []
    i = 0
    while i < len(text):
        out.append(text[i : i + max_chars])
        i += max_chars - overlap
    return out


def chunk_markdown(path: Path, text: str, source_root: Path) -> list[dict]:
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


def build(src: Path, db: Path) -> int:
    db.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(db))
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)

    # 幂等：重建 collection
    try:
        client.delete_collection(COLLECTION)
    except Exception:  # noqa: BLE001
        pass
    col = client.create_collection(COLLECTION, embedding_function=ef, metadata={"hnsw:space": "cosine"})

    all_chunks: list[dict] = []
    files = list(iter_markdown(src))
    print(f"[ingest] scanning {len(files)} md files under {src}")
    for p in files:
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = p.read_text(encoding="utf-8", errors="ignore")
        chunks = chunk_markdown(p, text, src)
        all_chunks.extend(chunks)

    print(f"[ingest] total chunks = {len(all_chunks)}")

    # 分批 add（Chroma 单次上限较大，稳妥起见 200/批）
    B = 200
    for i in range(0, len(all_chunks), B):
        batch = all_chunks[i : i + B]
        col.add(
            ids=[c["id"] for c in batch],
            documents=[c["content"] for c in batch],
            metadatas=[c["metadata"] for c in batch],
        )
        print(f"  + added {i + len(batch)}/{len(all_chunks)}")

    print(f"[ingest] done. collection={COLLECTION} count={col.count()}")
    return col.count()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="Xiehaoyu-Agent/个人知识库")
    ap.add_argument("--db", default="rag/data/chroma")
    args = ap.parse_args()
    build(Path(args.src), Path(args.db))


if __name__ == "__main__":
    main()
