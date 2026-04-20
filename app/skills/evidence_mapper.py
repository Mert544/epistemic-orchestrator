from __future__ import annotations

from app.tools.external_search import CompositeSearchTool, SearchResult


class EvidenceMapper:
    def __init__(self, search_tool: CompositeSearchTool | None = None) -> None:
        self.search_tool = search_tool or CompositeSearchTool()

    def map(self, claim: str) -> dict:
        supporting = self.search_tool.search(claim, top_k=3)
        opposing = self.search_tool.search(f"evidence against {claim}", top_k=2)

        return {
            "evidence_for": self._render_results(supporting),
            "evidence_against": self._render_results(opposing),
            "sources_for": supporting,
            "sources_against": opposing,
        }

    def _render_results(self, results: list[SearchResult]) -> list[str]:
        rendered: list[str] = []
        for item in results:
            parts = [item.title.strip()]
            if item.snippet:
                parts.append(item.snippet.strip())
            if item.url:
                parts.append(item.url.strip())
            rendered.append(" | ".join(parts))
        return rendered
