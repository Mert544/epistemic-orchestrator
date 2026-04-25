from __future__ import annotations

from app.engine.fractal_5whys import FractalNode


class FractalMermaidExporter:
    """Export fractal 5-Whys trees as Mermaid flowcharts.

    Usage:
        exporter = FractalMermaidExporter()
        mermaid = exporter.export(tree)
        # Paste into GitHub markdown, Notion, etc.
    """

    def export(self, tree: FractalNode, direction: str = "TD") -> str:
        """Export a single fractal tree as Mermaid flowchart."""
        lines = [f"flowchart {direction}"]
        self._walk(tree, lines, parent_id=None)
        return "\n".join(lines)

    def export_batch(self, trees: list[FractalNode], direction: str = "TD") -> str:
        """Export multiple trees as a single Mermaid diagram."""
        lines = [f"flowchart {direction}"]
        for idx, tree in enumerate(trees):
            lines.append(f"    subgraph Finding_{idx} [{tree.question}]")
            self._walk(tree, lines, parent_id=None, prefix=f"f{idx}_")
            lines.append("    end")
        return "\n".join(lines)

    def _walk(self, node: FractalNode, lines: list[str], parent_id: str | None, prefix: str = "n") -> str:
        node_id = f"{prefix}{node.level}_{id(node)}"
        label = node.answer.replace('"', "'")[:60]
        shape = self._shape_for_level(node.level)
        color = self._color_for_confidence(node.confidence)
        lines.append(f'    {node_id}{shape}["{label}"]')
        if color:
            lines.append(f"    style {node_id} fill:{color}")
        if parent_id:
            lines.append(f"    {parent_id} --> {node_id}")
        for child in node.children:
            self._walk(child, lines, parent_id=node_id, prefix=prefix)
        return node_id

    def _shape_for_level(self, level: int) -> str:
        if level == 1:
            return "(("  # circle
        elif level == 2:
            return "{{"  # rhombus
        elif level == 3:
            return "[("  # stadium
        else:
            return "["  # rectangle

    def _color_for_confidence(self, confidence: float) -> str:
        if confidence >= 0.9:
            return "#fecaca"  # red-200
        elif confidence >= 0.7:
            return "#fed7aa"  # orange-200
        elif confidence >= 0.5:
            return "#fef08a"  # yellow-200
        elif confidence >= 0.3:
            return "#bfdbfe"  # blue-200
        return "#e5e7eb"  # gray-200
