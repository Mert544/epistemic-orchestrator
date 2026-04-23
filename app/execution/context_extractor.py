from __future__ import annotations

import ast
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class FileContext:
    target_file: str
    code_window: str
    imports: list[str] = field(default_factory=list)
    related_tests: list[str] = field(default_factory=list)
    surrounding_symbols: list[str] = field(default_factory=list)


@dataclass
class ContextExtractionResult:
    contexts: list[FileContext] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"contexts": [asdict(context) for context in self.contexts]}


class ContextExtractor:
    """Extract compact code windows around semantic patch targets."""

    def extract(
        self,
        project_root: str | Path,
        target_files: list[str],
        window_lines: int = 40,
    ) -> ContextExtractionResult:
        root = Path(project_root).resolve()
        contexts: list[FileContext] = []

        for rel_path in target_files[:3]:
            target = (root / rel_path).resolve()
            if not str(target).startswith(str(root)) or not target.exists():
                continue
            text = target.read_text(encoding="utf-8")
            lines = text.splitlines()
            imports = [line for line in lines[:20] if line.strip().startswith(("import ", "from "))][:10]
            symbols = self._extract_symbols(text)
            code_window = "\n".join(lines[:window_lines])
            related_tests = self._find_related_tests(root, rel_path)
            contexts.append(
                FileContext(
                    target_file=rel_path,
                    code_window=code_window,
                    imports=imports,
                    related_tests=related_tests,
                    surrounding_symbols=symbols,
                )
            )

        return ContextExtractionResult(contexts=contexts)

    def _extract_symbols(self, source: str) -> list[str]:
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return []
        symbols: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                symbols.append(node.name)
        return list(dict.fromkeys(symbols))[:12]

    def _find_related_tests(self, root: Path, rel_path: str) -> list[str]:
        stem = Path(rel_path).stem.replace("test_", "")
        tests_root = root / "tests"
        if not tests_root.exists():
            return []
        matches: list[str] = []
        for path in tests_root.rglob("test_*.py"):
            if stem in path.stem or stem in path.read_text(encoding="utf-8", errors="ignore"):
                matches.append(str(path.relative_to(root)))
        return matches[:5]
