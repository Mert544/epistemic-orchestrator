from pathlib import Path

from app.execution.semantic_patch_generator import SemanticPatchGenerator


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_add_docstring_transform(tmp_path: Path):
    _write(tmp_path / "app" / "math.py", "def add(a, b):\n    return a + b\n")
    generator = SemanticPatchGenerator()
    patch_plan = {"target_files": ["app/math.py"], "title": "Add docstrings", "task_id": "t-1"}

    result = generator.generate(project_root=tmp_path, patch_plan=patch_plan)

    assert result.transform_type == "add_docstring"
    assert len(result.patch_requests) == 1
    pr = result.patch_requests[0]
    assert pr["path"] == "app/math.py"
    assert '"""Add docstrings."""' in pr["new_content"]
    assert pr["expected_old_content"] == "def add(a, b):\n    return a + b\n"
    assert result.estimated_tokens > 0
    assert result.mode == "semantic"


def test_add_type_annotations_transform(tmp_path: Path):
    _write(tmp_path / "app" / "math.py", "def add(a, b):\n    return a + b\n")
    generator = SemanticPatchGenerator()
    patch_plan = {"target_files": ["app/math.py"], "title": "Add type annotations", "task_id": "t-2"}

    result = generator.generate(project_root=tmp_path, patch_plan=patch_plan)

    assert result.transform_type == "add_type_annotations"
    pr = result.patch_requests[0]
    assert "-> None:" in pr["new_content"]
    assert pr["expected_old_content"] is not None


def test_add_guard_clause_transform(tmp_path: Path):
    _write(tmp_path / "app" / "math.py", "def add(a, b):\n    return a + b\n")
    generator = SemanticPatchGenerator()
    patch_plan = {"target_files": ["app/math.py"], "title": "Add input validation guard", "task_id": "t-3"}

    result = generator.generate(project_root=tmp_path, patch_plan=patch_plan)

    assert result.transform_type == "add_guard_clause"
    pr = result.patch_requests[0]
    assert "if not a:" in pr["new_content"]
    assert "raise ValueError" in pr["new_content"]


def test_create_test_stub(tmp_path: Path):
    generator = SemanticPatchGenerator()
    patch_plan = {"target_files": ["tests/test_orders.py"], "title": "Close test gap", "task_id": "t-4"}

    result = generator.generate(project_root=tmp_path, patch_plan=patch_plan)

    assert result.transform_type == "create_test_stub"
    pr = result.patch_requests[0]
    assert pr["path"] == "tests/test_orders.py"
    assert "def test_orders_exists():" in pr["new_content"]
    assert pr["expected_old_content"] is None


def test_repair_test_assertion_transform(tmp_path: Path):
    _write(tmp_path / "tests" / "test_math.py", "def test_add():\n    assert 1 + 1 == 2\n")
    generator = SemanticPatchGenerator()
    patch_plan = {"target_files": ["tests/test_math.py"], "title": "Fix tests", "task_id": "t-5"}
    repair_context = {"failure_type": "test_failure"}

    result = generator.generate(project_root=tmp_path, patch_plan=patch_plan, repair_context=repair_context)

    assert result.transform_type == "repair_test_assertion"
    pr = result.patch_requests[0]
    assert 'Assertion failed: 1 + 1 == 2' in pr["new_content"]


def test_fallback_when_no_target_files(tmp_path: Path):
    generator = SemanticPatchGenerator()
    patch_plan = {"target_files": [], "title": "Refactor everything", "task_id": "t-6"}

    result = generator.generate(project_root=tmp_path, patch_plan=patch_plan)

    assert result.transform_type == "draft_fallback"
    assert result.mode == "draft"
    assert len(result.rationale) >= 1


def test_does_not_duplicate_existing_docstring(tmp_path: Path):
    source = 'def add(a, b):\n    """Already documented."""\n    return a + b\n'
    _write(tmp_path / "app" / "math.py", source)
    generator = SemanticPatchGenerator()
    patch_plan = {"target_files": ["app/math.py"], "title": "Add docstrings", "task_id": "t-7"}

    result = generator.generate(project_root=tmp_path, patch_plan=patch_plan)

    # Should fall back to draft because no function without docstring found
    assert result.transform_type == "draft_fallback"


def test_expected_old_content_for_safety(tmp_path: Path):
    _write(tmp_path / "app" / "math.py", "def add(a, b):\n    return a + b\n")
    generator = SemanticPatchGenerator()
    patch_plan = {"target_files": ["app/math.py"], "title": "Add docstrings", "task_id": "t-8"}

    result = generator.generate(project_root=tmp_path, patch_plan=patch_plan)

    pr = result.patch_requests[0]
    assert pr["expected_old_content"] is not None
    assert pr["expected_old_content"] == "def add(a, b):\n    return a + b\n"


def test_scope_reduction_in_repair_mode(tmp_path: Path):
    _write(tmp_path / "app" / "a.py", "def a():\n    pass\n")
    _write(tmp_path / "app" / "b.py", "def b():\n    pass\n")
    _write(tmp_path / "app" / "c.py", "def c():\n    pass\n")
    generator = SemanticPatchGenerator()
    patch_plan = {
        "target_files": ["app/a.py", "app/b.py", "app/c.py"],
        "title": "Add docstrings",
        "task_id": "t-9",
    }
    repair_context = {"failure_type": "patch_scope_failure"}

    result = generator.generate(project_root=tmp_path, patch_plan=patch_plan, repair_context=repair_context)

    # Should only process first 3 (which is all of them here), but the logic is:
    # for rel_path in target_files (already limited to [:3] in repair mode)
    # It should still work and add docstring to first file
    assert result.transform_type == "add_docstring"
    assert result.patch_requests[0]["path"] == "app/a.py"
