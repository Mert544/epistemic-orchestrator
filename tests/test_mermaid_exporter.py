from __future__ import annotations

import pytest

from app.reporting.mermaid_exporter import FractalMermaidExporter
from app.engine.fractal_5whys import FractalNode


class TestFractalMermaidExporter:
    def test_export_single_tree(self):
        exporter = FractalMermaidExporter()
        root = FractalNode(level=1, question="Q?", answer="RCE", confidence=1.0)
        child = FractalNode(level=2, question="Why?", answer="Convenience", confidence=0.9)
        root.children.append(child)
        mermaid = exporter.export(root)
        assert "flowchart TD" in mermaid
        assert "RCE" in mermaid
        assert "Convenience" in mermaid
        assert "-->" in mermaid

    def test_export_batch(self):
        exporter = FractalMermaidExporter()
        trees = [
            FractalNode(level=1, question="Q1?", answer="A1", confidence=1.0),
            FractalNode(level=1, question="Q2?", answer="A2", confidence=1.0),
        ]
        mermaid = exporter.export_batch(trees)
        assert "subgraph Finding_0" in mermaid
        assert "subgraph Finding_1" in mermaid

    def test_color_for_confidence(self):
        exporter = FractalMermaidExporter()
        assert exporter._color_for_confidence(1.0) == "#fecaca"
        assert exporter._color_for_confidence(0.8) == "#fed7aa"
        assert exporter._color_for_confidence(0.4) == "#bfdbfe"
        assert exporter._color_for_confidence(0.1) == "#e5e7eb"

    def test_shape_for_level(self):
        exporter = FractalMermaidExporter()
        assert exporter._shape_for_level(1) == "(("
        assert exporter._shape_for_level(2) == "{{"
        assert exporter._shape_for_level(3) == "[("
        assert exporter._shape_for_level(4) == "["
