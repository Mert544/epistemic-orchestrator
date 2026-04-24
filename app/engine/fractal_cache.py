from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from app.engine.fractal_5whys import FractalNode


class FractalCache:
    """Persistent cache for fractal analysis trees.

    Avoids re-analyzing identical findings across runs.
    Cache key = SHA256(issue + file + line).
    """

    def __init__(self, cache_dir: str = ".apex/fractal_cache") -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key(self, finding: dict[str, Any]) -> str:
        raw = f"{finding.get('issue','')}:{finding.get('file','')}:{finding.get('line',0)}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def get(self, finding: dict[str, Any]) -> FractalNode | None:
        key = self._key(finding)
        path = self._path(key)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return self._deserialize(data)
        except Exception:
            return None

    def put(self, finding: dict[str, Any], tree: FractalNode) -> None:
        key = self._key(finding)
        path = self._path(key)
        path.write_text(json.dumps(tree.to_dict(), indent=2), encoding="utf-8")

    def invalidate(self, finding: dict[str, Any]) -> None:
        key = self._key(finding)
        path = self._path(key)
        if path.exists():
            path.unlink()

    def clear(self) -> None:
        for p in self.cache_dir.glob("*.json"):
            p.unlink()

    def _deserialize(self, data: dict[str, Any]) -> FractalNode:
        node = FractalNode(
            level=data["level"],
            question=data["question"],
            answer=data["answer"],
            confidence=data["confidence"],
            evidence=data.get("evidence", []),
            counter_evidence=data.get("counter_evidence", []),
            rebuttal=data.get("rebuttal", ""),
            metadata=data.get("metadata", {}),
        )
        for child_data in data.get("children", []):
            node.children.append(self._deserialize(child_data))
        return node
