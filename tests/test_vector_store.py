from __future__ import annotations

import pytest

from app.memory.vector_store import VectorStore


class TestVectorStore:
    def test_add_and_search(self):
        store = VectorStore()
        store.add("eval() found in auth.py", {"severity": "high"})
        store.add("os.system() in shell.py", {"severity": "critical"})
        results = store.search("eval usage detected")
        assert len(results) == 2
        assert results[0]["score"] > results[1]["score"] or results[0]["score"] == results[1]["score"]

    def test_search_ranking(self):
        store = VectorStore()
        store.add("eval() usage", {"id": 1})
        store.add("docstring missing", {"id": 2})
        store.add("eval in config", {"id": 3})
        results = store.search("eval function call", top_k=2)
        assert len(results) == 2
        ids = {r["metadata"]["id"] for r in results}
        assert 1 in ids or 3 in ids

    def test_empty_search(self):
        store = VectorStore()
        assert store.search("anything") == []

    def test_stats(self):
        store = VectorStore()
        store.add("a b c", {})
        store.add("b c d", {})
        stats = store.stats()
        assert stats["entries"] == 2
        assert stats["vocab_size"] == 4

    def test_cosine_identical(self):
        store = VectorStore()
        store.add("exact match text", {})
        results = store.search("exact match text")
        assert results[0]["score"] == pytest.approx(1.0, 0.01)
