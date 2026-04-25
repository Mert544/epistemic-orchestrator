from __future__ import annotations

from pathlib import Path

import pytest

from app.engine.action_executor import ActionExecutor, ActionResult
from app.engine.fractal_patch_generator import FractalPatch


class TestActionExecutor:
    def test_create_sandbox(self, tmp_path: Path):
        project = tmp_path / "project"
        project.mkdir()
        (project / "main.py").write_text("x = 1\n")
        executor = ActionExecutor(str(project))
        sandbox = executor.create_sandbox()
        assert sandbox.exists()
        assert (sandbox / "main.py").exists()
        # Original should be untouched
        assert (project / "main.py").exists()
        executor.cleanup()

    def test_execute_patch(self, tmp_path: Path):
        project = tmp_path / "project"
        project.mkdir()
        (project / "main.py").write_text("x = eval(y)\n")
        executor = ActionExecutor(str(project))
        patch = FractalPatch(
            file="main.py",
            finding="eval",
            action="replace",
            old_code="eval(y)",
            new_code="ast.literal_eval(y)",
            confidence=0.9,
        )
        result = executor.execute_patch(patch, run_tests=False)
        assert result.success is True
        assert result.changed_files == ["main.py"]
        # Sandbox should have patch
        sandbox_file = executor.sandbox_dir / "main.py"
        assert "ast.literal_eval" in sandbox_file.read_text()
        # Original should be unchanged
        assert "eval(y)" in (project / "main.py").read_text()
        executor.cleanup()

    def test_promote_to_original(self, tmp_path: Path):
        project = tmp_path / "project"
        project.mkdir()
        (project / "main.py").write_text("x = eval(y)\n")
        executor = ActionExecutor(str(project))
        patch = FractalPatch(
            file="main.py",
            finding="eval",
            action="replace",
            old_code="eval(y)",
            new_code="ast.literal_eval(y)",
            confidence=0.9,
        )
        executor.execute_patch(patch, run_tests=False)
        ok = executor.promote_to_original()
        assert ok is True
        assert "ast.literal_eval" in (project / "main.py").read_text()
        executor.cleanup()
