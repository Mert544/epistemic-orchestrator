from __future__ import annotations

from pathlib import Path

from app.agents.skills.docstring_agent import DocstringAgent


def test_docstring_agent_finds_gaps(tmp_path: Path):
    agent = DocstringAgent()
    (tmp_path / "test.py").write_text("def hello():\n    pass\n")
    result = agent.run(project_root=str(tmp_path))
    assert result["gaps_found"] >= 1
    assert any(g["name"] == "hello" for g in result["gaps"])


def test_docstring_agent_patches(tmp_path: Path):
    agent = DocstringAgent()
    (tmp_path / "test.py").write_text("def hello():\n    pass\n")
    result = agent.run(project_root=str(tmp_path), patch=True)
    assert len(result["patched_files"]) >= 1
    content = (tmp_path / "test.py").read_text()
    assert '"""' in content


def test_docstring_agent_respects_existing(tmp_path: Path):
    agent = DocstringAgent()
    (tmp_path / "test.py").write_text('def hello():\n    """Already documented."""\n    pass\n')
    result = agent.run(project_root=str(tmp_path))
    assert result["gaps_found"] == 0
