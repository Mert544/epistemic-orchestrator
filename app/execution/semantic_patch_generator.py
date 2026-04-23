from __future__ import annotations

import ast
import textwrap
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.execution.context_extractor import ContextExtractor
from app.execution.edit_strategy import EditStrategy
from app.execution.target_selector import TargetSelector


@dataclass
class SemanticPatchResult:
    patch_requests: list[dict[str, Any]] = field(default_factory=list)
    transform_type: str = "none"
    rationale: list[str] = field(default_factory=list)
    estimated_tokens: int = 0
    mode: str = "semantic"
    selected_targets: list[dict[str, Any]] = field(default_factory=list)
    extracted_contexts: list[dict[str, Any]] = field(default_factory=list)
    chosen_strategy: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SemanticPatchGenerator:
    """Generate real, small code changes using AST-based transforms.

    Design principles:
    - One transform per call, minimal surface area.
    - expected_old_content is always set for safety.
    - If file state changed since read, patch is skipped (ApplyPatchSkill handles this).
    - Falls back to draft mode only when no semantic transform applies.
    - Uses explicit target selection, context extraction, and edit-strategy choice.
    """

    def __init__(self) -> None:
        self.target_selector = TargetSelector()
        self.context_extractor = ContextExtractor()
        self.edit_strategy = EditStrategy()

    def generate(
        self,
        project_root: str | Path,
        patch_plan: dict[str, Any],
        task: dict[str, Any] | None = None,
        repair_context: dict[str, Any] | None = None,
        project_profile: dict[str, Any] | None = None,
    ) -> SemanticPatchResult:
        root = Path(project_root).resolve()
        task = task or {}
        repair = repair_context or {}
        title = str(patch_plan.get("title", task.get("title", "Unnamed task")))
        task_id = str(patch_plan.get("task_id", task.get("id", "task-0")))
        branch = patch_plan.get("branch") or task.get("branch") or "x.unknown"

        selection = self.target_selector.select(
            project_root=root,
            patch_plan=patch_plan,
            task=task,
            project_profile=project_profile,
        )
        target_files = [target.path for target in selection.targets]
        contexts = self.context_extractor.extract(root, target_files)
        related_tests: list[str] = []
        if contexts.contexts:
            related_tests = contexts.contexts[0].related_tests

        strategy = self.edit_strategy.choose(
            title=title,
            patch_plan=patch_plan,
            related_tests=related_tests,
            repair_context=repair,
        )

        if repair.get("failure_type") == "patch_scope_failure":
            target_files = target_files[:3]

        if not target_files:
            result = self._fallback_draft(root, task_id, title, branch, patch_plan, reason="No target files.")
            return self._attach_metadata(result, selection, contexts, strategy)

        for rel_path in target_files:
            target = (root / rel_path).resolve()
            if not str(target).startswith(str(root)):
                continue
            if not target.exists():
                stub = self._try_create_stub(root, rel_path, title, task_id)
                if stub:
                    return self._attach_metadata(self._estimate_and_return(stub), selection, contexts, strategy)
                continue

            if target.suffix.lower() != ".py":
                continue

            current = target.read_text(encoding="utf-8")
            transform = strategy.strategy

            if transform == "add_docstring":
                result = self._transform_add_docstring(rel_path, current, title)
                if result:
                    return self._attach_metadata(self._estimate_and_return(result), selection, contexts, strategy)

            if transform == "add_type_annotations":
                result = self._transform_add_type_annotations(rel_path, current, title)
                if result:
                    return self._attach_metadata(self._estimate_and_return(result), selection, contexts, strategy)

            if transform == "add_guard_clause":
                result = self._transform_add_guard_clause(rel_path, current, title)
                if result:
                    return self._attach_metadata(self._estimate_and_return(result), selection, contexts, strategy)

            if transform == "repair_test_assertion":
                result = self._transform_repair_test(rel_path, current, repair)
                if result:
                    return self._attach_metadata(self._estimate_and_return(result), selection, contexts, strategy)

            if transform == "rename_variable":
                rename_cfg = patch_plan.get("rename", {})
                result = self._transform_rename_variable(
                    rel_path, current, rename_cfg.get("old_name", ""),
                    rename_cfg.get("new_name", ""), rename_cfg.get("target_function", ""),
                )
                if result:
                    return self._attach_metadata(self._estimate_and_return(result), selection, contexts, strategy)

            if transform == "extract_method":
                extract_cfg = patch_plan.get("extract", {})
                result = self._transform_extract_method(
                    rel_path, current,
                    extract_cfg.get("start_line", 0),
                    extract_cfg.get("end_line", 0),
                    extract_cfg.get("new_function_name", ""),
                    extract_cfg.get("target_function", ""),
                    extract_cfg.get("parameters", []),
                )
                if result:
                    return self._attach_metadata(self._estimate_and_return(result), selection, contexts, strategy)

            if transform == "inline_variable":
                inline_cfg = patch_plan.get("inline", {})
                result = self._transform_inline_variable(
                    rel_path, current,
                    inline_cfg.get("var_name", ""),
                    inline_cfg.get("target_function", ""),
                )
                if result:
                    return self._attach_metadata(self._estimate_and_return(result), selection, contexts, strategy)

            if transform == "organize_imports":
                result = self._transform_organize_imports(rel_path, current)
                if result:
                    return self._attach_metadata(self._estimate_and_return(result), selection, contexts, strategy)

            if transform == "move_class":
                move_cfg = patch_plan.get("move", {})
                result = self._transform_move_class(
                    rel_path, current,
                    move_cfg.get("class_name", ""),
                    move_cfg.get("new_module", ""),
                )
                if result:
                    return self._attach_metadata(self._estimate_and_return(result), selection, contexts, strategy)

            if transform == "extract_class":
                extract_cfg = patch_plan.get("extract_class", {})
                result = self._transform_extract_class(
                    rel_path, current,
                    extract_cfg.get("methods", []),
                    extract_cfg.get("new_class_name", ""),
                    extract_cfg.get("base_class", None),
                )
                if result:
                    return self._attach_metadata(self._estimate_and_return(result), selection, contexts, strategy)

        result = self._fallback_draft(
            root, task_id, title, branch, patch_plan,
            reason="No safe semantic transform matched target files.",
        )
        return self._attach_metadata(result, selection, contexts, strategy)

    def _attach_metadata(
        self,
        result: SemanticPatchResult,
        selection,
        contexts,
        strategy,
    ) -> SemanticPatchResult:
        result.selected_targets = selection.to_dict()["targets"]
        result.extracted_contexts = contexts.to_dict()["contexts"]
        result.chosen_strategy = strategy.to_dict()
        result.rationale = [
            *strategy.reasons,
            *result.rationale,
        ]
        return result

    def _transform_add_docstring(self, rel_path: str, source: str, title: str) -> SemanticPatchResult | None:
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return None

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if ast.get_docstring(node) is None:
                    lines = source.splitlines(keepends=True)
                    lineno = node.lineno - 1
                    indent = self._get_indent(lines[lineno]) if lineno < len(lines) else ""
                    body_indent = indent + "    "
                    docstring = f'{body_indent}"""{title.strip(".")}."""\n'
                    insert_at = lineno + 1
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
                    stripped = line.rstrip()
                    if stripped.endswith(":") and "->" not in stripped:
                        new_line = stripped[:-1] + " -> None:\n"
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
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return None

        lines = source.splitlines(keepends=True)
        modified = False

        for node in ast.walk(tree):
            if isinstance(node, ast.Assert) and node.msg is None:
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

    def _transform_rename_variable(
        self, rel_path: str, source: str, old_name: str, new_name: str, target_function: str
    ) -> SemanticPatchResult | None:
        if not old_name or not new_name or not target_function:
            return None
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return None

        class RenameTransformer(ast.NodeTransformer):
            def __init__(self, target: str, old: str, new: str):
                self.target = target
                self.old = old
                self.new = new
                self.in_target = False
                self.nested_depth = 0
                self.changed = False

            def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:  # type: ignore[misc]
                if node.name == self.target and self.nested_depth == 0:
                    self.in_target = True
                    self.nested_depth += 1
                    result = self.generic_visit(node)
                    self.in_target = False
                    self.nested_depth -= 1
                    return result
                if self.in_target:
                    return node
                return self.generic_visit(node)

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:  # type: ignore[misc]
                return self.visit_FunctionDef(node)  # type: ignore[arg-type]

            def visit_Name(self, node: ast.Name) -> ast.Name:
                if self.in_target and node.id == self.old:
                    node.id = self.new
                    self.changed = True
                return node

            def visit_arg(self, node: ast.arg) -> ast.arg:
                if self.in_target and node.arg == self.old:
                    node.arg = self.new
                    self.changed = True
                return node

        transformer = RenameTransformer(target_function, old_name, new_name)
        new_tree = transformer.visit(tree)
        if not transformer.changed:
            return None
        try:
            new_source = ast.unparse(new_tree)
        except Exception:
            return None
        if source.endswith("\n") and not new_source.endswith("\n"):
            new_source += "\n"
        return SemanticPatchResult(
            patch_requests=[{
                "path": rel_path,
                "new_content": new_source,
                "expected_old_content": source,
            }],
            transform_type="rename_variable",
            rationale=[f"Renamed '{old_name}' -> '{new_name}' in {target_function} ({rel_path})."],
        )

    def _transform_extract_method(
        self, rel_path: str, source: str, start_line: int, end_line: int,
        new_function_name: str, target_function: str, parameters: list[str]
    ) -> SemanticPatchResult | None:
        if start_line < 1 or end_line < start_line or not new_function_name or not target_function:
            return None
        lines = source.splitlines(keepends=True)
        if end_line > len(lines):
            return None
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return None

        target_node = None
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == target_function:
                target_node = node
                break
        if target_node is None:
            return None

        start_idx = start_line - 1
        end_idx = end_line - 1
        block_lines = lines[start_idx:end_idx + 1]
        if not block_lines:
            return None

        indents = [len(self._get_indent(line)) for line in block_lines if line.strip()]
        if not indents:
            return None
        min_indent = min(indents)
        base_indent = self._get_indent(lines[target_node.lineno - 1])
        body_indent = base_indent + "    "

        normalized_block = []
        for line in block_lines:
            if line.strip():
                normalized_block.append(line[min_indent:])
            else:
                normalized_block.append("\n")

        return_var = ""
        try:
            block_tree = ast.parse("".join(normalized_block))
            for node in ast.walk(block_tree):
                if isinstance(node, ast.Assign) and node.targets and isinstance(node.targets[0], ast.Name):
                    return_var = node.targets[0].id
        except SyntaxError:
            pass

        param_str = ", ".join(parameters) if parameters else ""
        new_func_lines = [f"{base_indent}def {new_function_name}({param_str}):\n"]
        for line in normalized_block:
            if line.endswith("\n"):
                new_func_lines.append(body_indent + line)
            else:
                new_func_lines.append(body_indent + line + "\n")
        if return_var:
            new_func_lines.append(f"{body_indent}    return {return_var}\n")
        new_func_lines.append("\n")

        if return_var:
            call_line = f"{body_indent}{return_var} = {new_function_name}({param_str})\n"
        else:
            call_line = f"{body_indent}{new_function_name}({param_str})\n"

        insert_at = target_node.lineno - 1
        new_lines = lines[:insert_at] + new_func_lines + lines[insert_at:start_idx] + [call_line] + lines[end_idx + 1:]
        new_content = "".join(new_lines)

        return SemanticPatchResult(
            patch_requests=[{
                "path": rel_path,
                "new_content": new_content,
                "expected_old_content": source,
            }],
            transform_type="extract_method",
            rationale=[f"Extracted lines {start_line}-{end_line} into {new_function_name} in {rel_path}."],
        )

    def _transform_inline_variable(
        self, rel_path: str, source: str, var_name: str, target_function: str
    ) -> SemanticPatchResult | None:
        if not var_name or not target_function:
            return None
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return None

        class InlineTransformer(ast.NodeTransformer):
            def __init__(self, target: str, var: str):
                self.target = target
                self.var = var
                self.in_target = False
                self.assignment_node: ast.Assign | None = None
                self.changed = False

            def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:  # type: ignore[misc]
                if node.name == self.target:
                    self.in_target = True
                    result = self.generic_visit(node)
                    self.in_target = False
                    if self.assignment_node and isinstance(result, ast.FunctionDef):
                        result.body = [s for s in result.body if s is not self.assignment_node]
                        self.changed = True
                    return result
                return self.generic_visit(node)

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:  # type: ignore[misc]
                return self.visit_FunctionDef(node)  # type: ignore[arg-type]

            def visit_Name(self, node: ast.Name) -> ast.AST:
                if self.in_target and self.assignment_node and node.id == self.var:
                    return self.assignment_node.value
                return node

            def visit_Assign(self, node: ast.Assign) -> ast.AST:
                if self.in_target and not self.assignment_node:
                    if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id == self.var:
                        if isinstance(node.value, (ast.Name, ast.Constant, ast.BinOp)):
                            self.assignment_node = node
                            return node
                return self.generic_visit(node)

        transformer = InlineTransformer(target_function, var_name)
        new_tree = transformer.visit(tree)
        if not transformer.changed or transformer.assignment_node is None:
            return None
        try:
            new_source = ast.unparse(new_tree)
        except Exception:
            return None
        if source.endswith("\n") and not new_source.endswith("\n"):
            new_source += "\n"
        return SemanticPatchResult(
            patch_requests=[{
                "path": rel_path,
                "new_content": new_source,
                "expected_old_content": source,
            }],
            transform_type="inline_variable",
            rationale=[f"Inlined variable '{var_name}' in {target_function} ({rel_path})."],
        )

    def _transform_organize_imports(self, rel_path: str, source: str) -> SemanticPatchResult | None:
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return None

        used_names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                used_names.add(node.value.id)

        unused_lines: set[int] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                all_unused = True
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.asname or alias.name.split(".")[0]
                        if name in used_names:
                            all_unused = False
                            break
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        name = alias.asname or alias.name
                        if name in used_names:
                            all_unused = False
                            break
                    if module.split(".")[0] in used_names:
                        all_unused = False
                if all_unused:
                    for lineno in range(node.lineno, getattr(node, "end_lineno", node.lineno) + 1):
                        unused_lines.add(lineno)

        if not unused_lines:
            return None

        lines = source.splitlines(keepends=True)
        new_lines = [line for i, line in enumerate(lines, start=1) if i not in unused_lines]
        new_content = "".join(new_lines)
        return SemanticPatchResult(
            patch_requests=[{
                "path": rel_path,
                "new_content": new_content,
                "expected_old_content": source,
            }],
            transform_type="organize_imports",
            rationale=[f"Removed {len(unused_lines)} unused import lines in {rel_path}."],
        )

    def _transform_move_class(
        self, rel_path: str, source: str, class_name: str, new_module: str
    ) -> SemanticPatchResult | None:
        if not class_name or not new_module:
            return None
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return None

        class_nodes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == class_name]
        if not class_nodes:
            return None
        class_node = class_nodes[0]
        lines = source.splitlines(keepends=True)
        start = class_node.lineno - 1
        end = getattr(class_node, "end_lineno", class_node.lineno)
        class_text = "".join(lines[start:end])
        if not class_text.endswith("\n"):
            class_text += "\n"

        module_path = new_module.replace('/', '.').replace('\\', '.').rstrip('.py')
        import_line = f"from {module_path} import {class_name}\n"
        new_source = "".join(lines[:start] + [import_line] + lines[end:])

        return SemanticPatchResult(
            patch_requests=[
                {
                    "path": rel_path,
                    "new_content": new_source,
                    "expected_old_content": source,
                },
                {
                    "path": new_module,
                    "new_content": class_text,
                    "expected_old_content": None,
                },
            ],
            transform_type="move_class",
            rationale=[f"Moved class '{class_name}' to {new_module} and replaced with import."],
        )

    def _transform_extract_class(
        self, rel_path: str, source: str, methods: list[str], new_class_name: str, base_class: str | None
    ) -> SemanticPatchResult | None:
        if not methods or not new_class_name:
            return None
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return None

        target_class = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                target_class = node
                break
        if target_class is None:
            return None

        lines = source.splitlines(keepends=True)
        extracted_methods = []
        base_indent = self._get_indent(lines[target_class.lineno - 1]) if target_class.lineno - 1 < len(lines) else ""
        body_indent = base_indent + "    "

        for item in target_class.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name in methods:
                start = item.lineno - 1
                end = getattr(item, "end_lineno", item.lineno)
                method_lines = lines[start:end]
                normalized = []
                for line in method_lines:
                    if line.strip():
                        normalized.append(line[len(body_indent):] if line.startswith(body_indent) else line)
                    else:
                        normalized.append("\n")
                extracted_methods.extend(normalized)

        if not extracted_methods:
            return None

        base = f"({base_class})" if base_class else ""
        new_class_lines = [f"{base_indent}class {new_class_name}{base}:\n"]
        for line in extracted_methods:
            new_class_lines.append(body_indent + line)
        if not new_class_lines[-1].endswith("\n"):
            new_class_lines[-1] += "\n"
        new_class_text = "".join(new_class_lines)

        class_start = target_class.lineno - 1
        new_source = "".join(lines[:class_start] + [new_class_text + "\n"] + lines[class_start:])

        return SemanticPatchResult(
            patch_requests=[{
                "path": rel_path,
                "new_content": new_source,
                "expected_old_content": source,
            }],
            transform_type="extract_class",
            rationale=[f"Extracted methods {methods} into class '{new_class_name}' in {rel_path}."],
        )

    def _estimate_and_return(self, result: SemanticPatchResult) -> SemanticPatchResult:
        total_chars = sum(len(pr["new_content"]) for pr in result.patch_requests)
        context_chars = sum(len(ctx.get("code_window", "")) for ctx in result.extracted_contexts)
        result.estimated_tokens = (total_chars + context_chars) // 4
        return result

    @staticmethod
    def _get_indent(line: str) -> str:
        stripped = line.lstrip()
        if stripped:
            return line[: line.index(stripped)]
        return line
