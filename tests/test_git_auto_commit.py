from __future__ import annotations

from pathlib import Path

import pytest

from app.engine.git_auto_commit import GitAutoCommit


class TestGitAutoCommit:
    def test_not_git_repo(self, tmp_path: Path):
        gac = GitAutoCommit(str(tmp_path))
        result = gac.commit(["file.py"], finding="eval() usage")
        assert result.success is False
        assert "Not a git repository" in result.error

    def test_build_message_security(self):
        gac = GitAutoCommit()
        msg = gac._build_message("eval() usage", "fix", ["auth.py"])
        assert msg.startswith("security:")
        assert "eval" in msg
        assert "auth.py" in msg

    def test_build_message_docs(self):
        gac = GitAutoCommit()
        msg = gac._build_message("missing_docstring", "fix", ["utils.py"])
        assert msg.startswith("docs:")
        assert "docstring" in msg

    def test_build_message_test(self):
        gac = GitAutoCommit()
        msg = gac._build_message("missing_test", "generate", ["test_main.py"])
        assert msg.startswith("test:")
        assert "test" in msg
