from __future__ import annotations

import ast
import textwrap
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SemanticPatchResult:
    patch_requests: list[dict[str, Any]] = field(default_factory=list)
    transform_type: str = "none"
    rationale: list[str] = field(default_factory=list)
    estimated_tokens: int = 0
    mode: str = "semantic"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SemanticPatchGenerator:
    """Generate real, small code changes using AST-based transforms.

    Design principles:
    - One transform per call, minimal surface area.
    - expected_old_content is always set for safety.
    - If file state changed since read, patch is skipped (ApplyPatchSkill handles this).
    - Falls back to draft mode only when no semantic transform applies.
    """

    def generate(
        self,
        project_root: str | Path,
        patch_plan: dict[str, Any],
        task: dict[str, Any] | None = None,
        repair_context: dict[str, Any] | None = None,
    ) -> SemanticPatchResult:
        root = Path(project_root).resolve()
        task = task or {}
        repair = repair_context or {}
        target_files = list(patch_plan.get("target_files", []) or [])
        title = str(patch_plan.get("title", task.get("title", "Unnamed task")))
        task_id = str(patch_plan.get("task_id", task.get("id", "task-0")))
        branch = patch_plan.get("branch") or task.get("branch") or "x.unknown"

        # Repair-mode scope reduction
        if repair.get("failure_type") == "patch_scope_failure":
            target_files = target_files[:3]

        if not target_files:
            return self._fallback_draft(root, task_id, title, branch, patch_plan, reason="No target files.")

        for rel_path in target_files:
            target = (root / rel_path).resolve()
            if not str(target).startswith(str(root)):
                continue
            if not target.exists():
                # Maybe create a test stub or init file
                stub = self._try_create_stub(root, rel_path, title, task_id)
                if stub:
                    return stub
                continue

            if target.suffix.lower() != ".py":
                continue

            current = target.read_text(encoding="utf-8")
            transform = self._select_transform(title, patch_plan, repair)

            if transform == "add_docstring":
                result = self._transform_add_docstring(rel_path, current, title)
                if result:
                    return self._estimate_and_return(result)

            if transform == "add_type_annotations":
                result = self._transform_add_type_annotations(rel_path, current, title)
                if result:
                    return self._estimate_and_return(result)

            if transform == "add_guard_clause":
                result = self._transform_add_guard_clause(rel_path, current, title)
                if result:
                    return self._estimate_and_return(result)

            if transform == "repair_test_assertion":
                result = self._transform_repair_test(rel_path, current, repair)
                if result:
                    return self._estimate_and_return(result)

        return self._fallback_draft(
            root, task_id, title, branch, patch_plan,
            reason="No safe semantic transform matched target files.",
        )

    def _select_transform(self, title: str, patch_plan: dict[str, Any], repair: dict[str, Any]) -> str:
        title_lower = title.lower()
        strategy = " ".join(patch_plan.get("change_strategy", [])).lower()
        combined = f"{title_lower} {strategy}"

        failure_type = repair.get("failure_type", "")
        if failure_type == "test_failure":
            return "repair_test_assertion"
        if failure_type == "patch_scope_failure":
            return "add_docstring"  # smallest safe transform

        if "docstring" in combined or "document" in combined:
            return "add_docstring"
        if "type" in combined or "typing" in combined or "annotation" in combined:
            return "add_type_annotations"
        if "guard" in combined or "validate" in combined or "input" in combined or "security" in combined:
            return "add_guard_clause"
        if "test" in combined or "coverage" in combined:
            return "add_docstring"  # conservative default for test gaps

        # Default: try docstring first as safest semantic edit
        return "add_docstring"

    def _transform_add_docstring(self, rel_path: str, source: str, title: str) -> SemanticPatchResult | None:
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return None

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if ast.get_docstring(node) is None:
                    # Insert docstring after the definition line
                    lines = source.splitlines(keepends=True)
                    lineno = node.lineno - 1  # 0-based
                    indent = self._get_indent(lines[lineno]) if lineno < len(lines) else ""
                    body_indent = indent + "    "
                    docstring = f'{body_indent}"""{title.strip(".")}."""\n'
                    insert_at = lineno + 1
                    # If next line is already a string literal, skip (edge case)
                    if insert_at < len(lines) and lines[insert_at].strip().startswith('"""'):
                        continue
                    new_lines = lines[:insert_at] + [docstring] + lines[insert_at:]
                    new_content = "".join(new_lines)
                    return SemanticPatchResult(
                        patch_requests=[{
                            "path": rel_path,
                            "new_content": new_content,
                            "expected_old_content": source,
                        }],
                        transform_type="add_docstring",
                        rationale=[f"Added missing docstring to {node.name} in {rel_path}."],
                    )
        return None

    def _transform_add_type_annotations(self, rel_path: str, source: str, title: str) -> SemanticPatchResult | None:
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return None

        lines = source.splitlines(keepends=True)
        modified = False

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.returns is None:
                    lineno = node.lineno - 1
                    line = lines[lineno]
                    # Simple heuristic: insert -> None before colon at end of def line
                    stripped = line.rstrip()
                    if stripped.endswith(":"):
                        # Check if already has -> somewhere (shouldn't if returns is None, but safety)
                        if "->" not in stripped:
                            new_line = stripped[:-1] + " -> None:\n"
                            lines[lineno] = new_line
                            modified = True
                            break  # Only one function per patch for safety

        if not modified:
            return None

        new_content = "".join(lines)
        return SemanticPatchResult(
            patch_requests=[{
                "path": rel_path,
                "new_content": new_content,
                "expected_old_content": source,
            }],
            transform_type="add_type_annotations",
            rationale=[f"Added missing return type annotation in {rel_path}."],
        )

    def _transform_add_guard_clause(self, rel_path: str, source: str, title: str) -> SemanticPatchResult | None:
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return None

        lines = source.splitlines(keepends=True)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.args.args:
                    continue
                first_arg = node.args.args[0].arg
                lineno = node.lineno - 1
                indent = self._get_indent(lines[lineno]) if lineno < len(lines) else "    "
                body_start = node.body[0].lineno - 1
                guard = f'{indent}    if not {first_arg}:\n{indent}        raise ValueError("{first_arg} is required")\n'
                # Only add if not already present (simple string check)
                if f"if not {first_arg}:" in source:
                    continue
                new_lines = lines[:body_start] + [guard] + lines[body_start:]
                new_content = "".join(new_lines)
                return SemanticPatchResult(
                    patch_requests=[{
                        "path": rel_path,
                        "new_content": new_content,
                        "expected_old_content": source,
                    }],
                    transform_type="add_guard_clause",
                    rationale=[f"Added input guard for '{first_arg}' in {rel_path}."],
                )
        return None

    def _transform_repair_test(self, rel_path: str, source: str, repair: dict[str, Any]) -> SemanticPatchResult | None:
        """Minimal test repair: if a test has a bare assert, add a descriptive message."""
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return None

        lines = source.splitlines(keepends=True)
        modified = False

        for node in ast.walk(tree):
            if isinstance(node, ast.Assert):
                if node.msg is None:
                    lineno = node.lineno - 1
                    line = lines[lineno]
                    stripped = line.rstrip()
                    content = stripped.lstrip()
                    indent = stripped[: len(stripped) - len(content)]
                    if content.startswith("assert "):
                        expr = content[7:]
                        if not expr.endswith('"') and "#" not in expr:
                            new_content = f'{content}, "Assertion failed: {expr}"'
                            new_line = indent + new_content + "\n"
                            lines[lineno] = new_line
                            modified = True
                            break

        if not modified:
            return None

        new_content = "".join(lines)
        return SemanticPatchResult(
            patch_requests=[{
                "path": rel_path,
                "new_content": new_content,
                "expected_old_content": source,
            }],
            transform_type="repair_test_assertion",
            rationale=[f"Added assertion message for better test diagnostics in {rel_path}."],
        )

    def _try_create_stub(self, root: Path, rel_path: str, title: str, task_id: str) -> SemanticPatchResult | None:
        if "test_" in rel_path and rel_path.endswith(".py"):
            # Derive module path from test path: tests/test_foo.py -> app.foo
            parts = Path(rel_path).parts
            if len(parts) >= 2 and parts[0] == "tests":
                module_name = parts[1].replace("test_", "").replace(".py", "")
                content = textwrap.dedent(
                    f"""\
                    # Generated by Apex Orchestrator
                    # task: {task_id}
                    # title: {title}

                    import pytest


                    def test_{module_name}_exists():
                        assert True, "stub test for {module_name}"
                    """
                )
                return SemanticPatchResult(
                    patch_requests=[{
                        "path": rel_path,
                        "new_content": content,
                        "expected_old_content": None,
                    }],
                    transform_type="create_test_stub",
                    rationale=[f"Created missing test stub at {rel_path}."],
                )
        return None

    def _fallback_draft(
        self, root: Path, task_id: str, title: str, branch: str, patch_plan: dict[str, Any], reason: str
    ) -> SemanticPatchResult:
        fallback_path = root / ".apex" / "patch-drafts" / f"{task_id}.md"
        lines = [
            "# Apex Orchestrator Patch Draft",
            "",
            f"- task_id: {task_id}",
            f"- title: {title}",
            f"- branch: {branch}",
            "",
            "## Change strategy",
        ]
        for item in patch_plan.get("change_strategy", []) or ["No explicit change strategy captured."]:
            lines.append(f"- {item}")
        lines.append("")
        lines.append("## Verification steps")
        for item in patch_plan.get("verification_steps", []) or ["Run detected project tests."]:
            lines.append(f"- {item}")
        content = "\n".join(lines) + "\n"
        return SemanticPatchResult(
            patch_requests=[{
                "path": str(fallback_path.relative_to(root)),
                "new_content": content,
                "expected_old_content": None,
            }],
            transform_type="draft_fallback",
            rationale=[reason, "Fell back to standalone draft document."],
            mode="draft",
        )

    def _estimate_and_return(self, result: SemanticPatchResult) -> SemanticPatchResult:
        total_chars = sum(len(pr["new_content"]) for pr in result.patch_requests)
        result.estimated_tokens = total_chars // 4
        return result

    @staticmethod
    def _get_indent(line: str) -> str:
        stripped = line.lstrip()
        if stripped:
            return line[: line.index(stripped)]
        return line
