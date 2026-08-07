"""RAG module tests: chunking, embedding/retrieval, and edge cases.

Tests cover:
- ``rag/ingest.py``: ``split_by_heading``, ``hard_split``, ``chunk_markdown``
- ``rag/retriever.py``: ``retrieve()``, ``count()``, ``Hit`` dataclass
- Edge cases: empty input, missing collection, malformed documents
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from chromadb.errors import NotFoundError

from rag.ingest import (
    chunk_markdown,
    hard_split,
    split_by_heading,
)
from rag.retriever import Hit, count, retrieve


# ── split_by_heading tests ────────────────────────────────────


class TestSplitByHeading:
    def test_empty_string(self):
        assert split_by_heading("") == []

    def test_whitespace_only(self):
        assert split_by_heading("   \n  \n  ") == []

    def test_no_headings_returns_single_chunk(self):
        text = "This is a paragraph without any headings."
        chunks = split_by_heading(text)
        assert len(chunks) == 1
        assert chunks[0][0] == ""  # no heading path
        assert chunks[0][1] == "This is a paragraph without any headings."

    def test_single_h1(self):
        text = "# Introduction\n\nHello world."
        chunks = split_by_heading(text)
        assert len(chunks) == 1
        assert chunks[0][0] == "Introduction"
        assert "Hello world" in chunks[0][1]

    def test_h1_h2_hierarchy(self):
        text = (
            "# About Me\n"
            "I am a student.\n\n"
            "## Education\n"
            "University.\n\n"
            "## Projects\n"
            "Project A.\n"
        )
        chunks = split_by_heading(text)
        assert len(chunks) == 3
        assert chunks[0][0] == "About Me"
        assert chunks[1][0] == "About Me > Education"
        assert chunks[2][0] == "About Me > Projects"

    def test_h1_h2_h3_deep(self):
        text = (
            "# Resume\n"
            "Summary.\n\n"
            "## Experience\n"
            "Work history.\n\n"
            "### Company A\n"
            "Details.\n\n"
            "## Skills\n"
            "Tech skills.\n"
        )
        chunks = split_by_heading(text)
        paths = [c[0] for c in chunks]
        assert "Resume" in paths
        assert "Resume > Experience" in paths
        assert "Resume > Experience > Company A" in paths
        assert "Resume > Skills" in paths

    def test_preface_before_first_heading(self):
        text = "Some preface text.\n\n# Heading\n\nBody text."
        chunks = split_by_heading(text)
        assert len(chunks) == 2
        assert chunks[0][0] == ""
        assert "preface" in chunks[0][1]
        assert chunks[1][0] == "Heading"

    def test_heading_without_body(self):
        text = "# Title\n\n# Another Title\n\nBody here."
        chunks = split_by_heading(text)
        # Title heading has no body between it and the next heading, so it's skipped
        paths = [c[0] for c in chunks]
        assert "Another Title" in paths
        assert all("Body here" in c[1] for c in chunks if c[0] == "Another Title")

    def test_heading_level_reset(self):
        """H3 then H2: H2 pops the H3 stack entry."""
        text = (
            "# Top\n"
            "Top body.\n\n"
            "### Deep\n"
            "Deep body.\n\n"
            "## Middle\n"
            "Middle body.\n"
        )
        chunks = split_by_heading(text)
        paths = [c[0] for c in chunks]
        assert "Top" in paths
        assert "Top > Deep" in paths
        # After H2, H3 should be popped, so path is Top > Middle
        assert "Top > Middle" in paths

    def test_ignores_h4_and_deeper(self):
        text = (
            "# H1\n"
            "H1 body.\n\n"
            "#### H4 ignored\n"
            "H4 body.\n"
        )
        chunks = split_by_heading(text)
        # H4 is not matched by the regex (only H1-H3), so it's treated as body text
        assert len(chunks) == 1
        assert chunks[0][0] == "H1"
        assert "#### H4 ignored" in chunks[0][1]


# ── hard_split tests ──────────────────────────────────────────


class TestHardSplit:
    def test_short_text_not_split(self):
        result = hard_split("short", max_chars=800, overlap=80)
        assert result == ["short"]

    def test_exactly_max_chars(self):
        text = "a" * 800
        result = hard_split(text, max_chars=800, overlap=80)
        assert len(result) == 1
        assert result[0] == text

    def test_long_text_split(self):
        text = "a" * 2000
        result = hard_split(text, max_chars=800, overlap=80)
        assert len(result) == 3  # 800 + 720 + 480
        assert all(len(chunk) <= 800 for chunk in result)

    def test_overlap_preserves_context(self):
        text = "0123456789" * 100  # 1000 chars
        result = hard_split(text, max_chars=200, overlap=50)
        # Second chunk should start with content from the end of first chunk
        assert len(result) >= 5
        # Check overlap: last 50 chars of chunk 0 should equal first 50 chars of chunk 1
        assert result[0][-50:] == result[1][:50]

    def test_single_character_overlap(self):
        text = "a" * 100
        result = hard_split(text, max_chars=30, overlap=1)
        assert len(result) == 4  # 30 + 29 + 29 + 12
        for chunk in result:
            assert len(chunk) <= 30

    def test_overlap_not_exceeding_max_chars(self):
        """Each chunk must be at most max_chars, regardless of overlap."""
        text = "x" * 5000
        for max_chars in [100, 500, 800]:
            for overlap in [10, 80, 200]:
                result = hard_split(text, max_chars=max_chars, overlap=min(overlap, max_chars - 1))
                for i, chunk in enumerate(result):
                    assert len(chunk) <= max_chars, (
                        f"Chunk {i} has {len(chunk)} chars, max={max_chars}, overlap={overlap}"
                    )


# ── chunk_markdown tests ──────────────────────────────────────


class TestChunkMarkdown:
    @pytest.fixture
    def tmp_src(self):
        with tempfile.TemporaryDirectory() as td:
            yield Path(td)

    def test_empty_file_produces_no_chunks(self, tmp_src):
        p = tmp_src / "empty.md"
        p.write_text("", encoding="utf-8")
        chunks = chunk_markdown(p, "", tmp_src)
        assert chunks == []

    def test_single_paragraph(self, tmp_src):
        p = tmp_src / "简历" / "test.md"
        (tmp_src / "简历").mkdir(parents=True, exist_ok=True)
        p.write_text("This is a test paragraph.", encoding="utf-8")
        chunks = chunk_markdown(p, p.read_text(encoding="utf-8"), tmp_src)
        assert len(chunks) == 1
        assert chunks[0]["content"] == "This is a test paragraph."
        assert chunks[0]["metadata"]["source"] == "简历/test.md"

    def test_ids_are_unique(self, tmp_src):
        p = tmp_src / "test.md"
        text = "# A\n\n" + "x" * 2000  # long enough to produce multiple chunks
        p.write_text(text, encoding="utf-8")
        chunks = chunk_markdown(p, text, tmp_src)
        ids = [c["id"] for c in chunks]
        assert len(ids) == len(set(ids)), f"Duplicate IDs found: {ids}"

    def test_ids_contain_source_path(self, tmp_src):
        p = tmp_src / "简历" / "intro.md"
        (tmp_src / "简历").mkdir(parents=True, exist_ok=True)
        p.write_text("# Hello\n\nWorld.", encoding="utf-8")
        chunks = chunk_markdown(p, p.read_text(encoding="utf-8"), tmp_src)
        for c in chunks:
            assert "简历/intro.md" in c["id"]

    def test_heading_metadata(self, tmp_src):
        p = tmp_src / "test.md"
        p.write_text("# About\n\nContent.", encoding="utf-8")
        chunks = chunk_markdown(p, p.read_text(encoding="utf-8"), tmp_src)
        assert chunks[0]["metadata"]["heading"] == "About"

    def test_chunk_index_increments(self, tmp_src):
        p = tmp_src / "test.md"
        text = "# One\n\nbody1\n\n# Two\n\nbody2\n\n# Three\n\nbody3\n"
        p.write_text(text, encoding="utf-8")
        chunks = chunk_markdown(p, text, tmp_src)
        indices = [c["metadata"]["chunk_index"] for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_content_starts_with_hash_for_headed_chunks(self, tmp_src):
        p = tmp_src / "test.md"
        p.write_text("# Profile\n\nI am a developer.", encoding="utf-8")
        chunks = chunk_markdown(p, p.read_text(encoding="utf-8"), tmp_src)
        assert chunks[0]["content"].startswith("# Profile")


# ── Hit dataclass tests ───────────────────────────────────────


class TestHit:
    def test_similarity_computed_from_distance(self):
        h = Hit(content="test", source="a.md", heading="H1", distance=0.3)
        assert h.similarity == 0.7

    def test_similarity_zero_distance(self):
        h = Hit(content="test", source="a.md", heading="", distance=0.0)
        assert h.similarity == 1.0

    def test_similarity_max_distance(self):
        h = Hit(content="test", source="a.md", heading="", distance=2.0)
        assert h.similarity == -1.0  # cosine distance max is 2

    def test_similarity_rounded_to_4_decimal_places(self):
        h = Hit(content="test", source="a.md", heading="", distance=0.123456789)
        assert h.similarity == round(1.0 - 0.123456789, 4)


# ── retrieve() tests ──────────────────────────────────────────


class TestRetrieve:
    def test_returns_empty_list_when_collection_missing(self):
        """When ChromaDB can't find the collection, _get_collection raises."""
        with patch("rag.retriever._get_collection", side_effect=Exception("collection not found")):
            hits = retrieve("test query", top_k=5)
            assert hits == []

    def test_returns_empty_list_when_no_chunks_match(self):
        """When the collection exists but has no data, returns empty list."""
        with patch("rag.retriever._get_collection") as mock_col:
            mock_col.return_value.query.return_value = {
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]],
            }
            hits = retrieve("any query", top_k=5)
            assert hits == []

    def test_correct_number_of_hits(self):
        mock_docs = [["chunk1", "chunk2", "chunk3"]]
        mock_metas = [
            [
                {"source": "a.md", "heading": "H1"},
                {"source": "b.md", "heading": "H2"},
                {"source": "c.md", "heading": ""},
            ]
        ]
        mock_dists = [[0.1, 0.5, 0.9]]

        with patch("rag.retriever._get_collection") as mock_col:
            mock_col.return_value.query.return_value = {
                "documents": mock_docs,
                "metadatas": mock_metas,
                "distances": mock_dists,
            }
            hits = retrieve("query", top_k=3, min_similarity=0.0)

        assert len(hits) == 3
        assert hits[0].content == "chunk1"
        assert hits[0].source == "a.md"
        assert hits[0].heading == "H1"
        assert hits[0].distance == 0.1

    def test_hits_ordered_by_relevance(self):
        """ChromaDB returns results sorted by distance (best first).
        Our mock data must also be sorted best-first."""
        # Simulate what ChromaDB actually returns: best (lowest distance) first
        mock_docs = [["best", "middle", "least"]]
        mock_metas = [
            [
                {"source": "c.md", "heading": ""},
                {"source": "b.md", "heading": ""},
                {"source": "a.md", "heading": ""},
            ]
        ]
        mock_dists = [[0.1, 0.5, 0.9]]

        with patch("rag.retriever._get_collection") as mock_col:
            mock_col.return_value.query.return_value = {
                "documents": mock_docs,
                "metadatas": mock_metas,
                "distances": mock_dists,
            }
            hits = retrieve("query", top_k=3, min_similarity=0.0)

        assert hits[0].distance == 0.1
        assert hits[1].distance == 0.5
        assert hits[2].distance == 0.9

    def test_get_collection_error_returns_empty(self):
        with patch("rag.retriever._get_collection", side_effect=RuntimeError("disk full")):
            hits = retrieve("query")
            assert hits == []

    def test_query_error_returns_empty(self):
        with patch("rag.retriever._get_collection") as mock_col:
            mock_col.return_value.query.side_effect = RuntimeError("query failed")
            hits = retrieve("query")
            assert hits == []

    def test_retries_once_after_collection_rebuilt(self):
        """ingest 在其它进程重建集合后，缓存句柄指向已删除的 UUID（NotFoundError）：
        应自动清缓存、按名字重取新集合并重试一次，调用方无感知。"""
        stale = MagicMock()
        stale.query.side_effect = NotFoundError("Collection [old-uuid] does not exist.")
        fresh = MagicMock()
        fresh.query.return_value = {
            "documents": [["chunk1"]],
            "metadatas": [[{"source": "a.md", "heading": "H1"}]],
            "distances": [[0.2]],
        }

        with patch("rag.retriever._get_collection") as mock_get:
            mock_get.side_effect = [stale, fresh]
            hits = retrieve("query", top_k=3, min_similarity=0.0)

        assert len(hits) == 1
        assert hits[0].content == "chunk1"
        assert stale.query.call_count == 1
        assert fresh.query.call_count == 1
        assert mock_get.call_count == 2

    def test_returns_empty_when_retry_also_fails(self):
        """刷新后重取仍失败（如集合尚未重建完）：按原逻辑降级返回空列表。"""
        stale = MagicMock()
        stale.query.side_effect = NotFoundError("gone")

        with patch("rag.retriever._get_collection") as mock_get:
            mock_get.side_effect = [stale, NotFoundError("still gone")]
            hits = retrieve("query")

        assert hits == []
        assert mock_get.call_count == 2

    def test_no_retry_on_non_not_found_error(self):
        """非 NotFoundError（如磁盘错误）不触发刷新重试，直接降级。"""
        with patch("rag.retriever._get_collection") as mock_get:
            mock_get.return_value.query.side_effect = RuntimeError("disk error")
            hits = retrieve("query")

        assert hits == []
        assert mock_get.call_count == 1


# ── count() tests ─────────────────────────────────────────────


class TestCount:
    def test_returns_zero_when_collection_missing(self):
        """When _get_collection raises, count() returns 0."""
        with patch("rag.retriever._get_collection", side_effect=Exception("no collection")):
            assert count() == 0

    def test_returns_zero_on_error(self):
        with patch("rag.retriever._get_collection", side_effect=Exception("boom")):
            assert count() == 0

    def test_returns_collection_count(self):
        with patch("rag.retriever._get_collection") as mock_col:
            mock_col.return_value.count.return_value = 42
            assert count() == 42


# ── chunk_markdown press/release of prior heading ──────────────


class TestChunkMarkdownEdgeCases:
    @pytest.fixture
    def tmp_src(self):
        with tempfile.TemporaryDirectory() as td:
            yield Path(td)

    def test_h1_then_h2_then_h1(self, tmp_src):
        """H2 should be nested under first H1, second H1 should reset."""
        p = tmp_src / "test.md"
        text = (
            "# Section A\n"
            "Body A.\n\n"
            "## Sub A\n"
            "Sub body.\n\n"
            "# Section B\n"
            "Body B.\n"
        )
        p.write_text(text, encoding="utf-8")
        chunks = chunk_markdown(p, text, tmp_src)
        headings = [c["metadata"]["heading"] for c in chunks]
        assert "Section A" in headings
        assert "Section A > Sub A" in headings
        assert "Section B" in headings
        # Section B should NOT be nested under Section A
        assert "Section A > Section B" not in headings

    def test_unicode_chinese_characters(self, tmp_src):
        p = tmp_src / "test.md"
        text = "# 个人简介\n\n我是谢浩宇，来自吉首大学。\n\n## 教育背景\n\n专业是数据科学。\n"
        p.write_text(text, encoding="utf-8")
        chunks = chunk_markdown(p, text, tmp_src)
        assert len(chunks) == 2
        assert "个人简介" in chunks[0]["metadata"]["heading"]
        assert "个人简介 > 教育背景" in chunks[1]["metadata"]["heading"]
        assert "谢浩宇" in chunks[0]["content"]
        assert "数据科学" in chunks[1]["content"]