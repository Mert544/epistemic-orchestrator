from pathlib import Path

from app.agents.skills import DocstringAgent


def _write(root: Path, rel: str, content: str) -> None:
    (root / rel).parent.mkdir(parents=True, exist_ok=True)
    (root / rel).write_text(content, encoding="utf-8")


def test_docstring_agent_finds_missing_docstrings(tmp_path: Path):
    _write(
        tmp_path,
        "app/main.py",
        'def hello():\n    """Existing docstring."""\n    pass\n\ndef world():\n    pass\n',
    )
    agent = DocstringAgent()
    result = agent.run(project_root=tmp_path)

    assert result["gaps_found"] == 1
    assert result["gaps"][0]["name"] == "world"
    assert result["total_symbols"] == 2


def test_docstring_agent_patches_missing_docstrings(tmp_path: Path):
    _write(
        tmp_path,
        "app/main.py",
        "def hello():\n    pass\n",
    )
    agent = DocstringAgent()
    result = agent.run(project_root=tmp_path, patch=True)

    assert "app/main.py" in result["patched_files"]
    content = (tmp_path / "app" / "main.py").read_text(encoding="utf-8")
    assert '"""hello implementation."""' in content


def test_docstring_agent_skips_existing_docstrings(tmp_path: Path):
    _write(
        tmp_path,
        "app/main.py",
        'def hello():\n    """Already here."""\n    pass\n',
    )
    agent = DocstringAgent()
    result = agent.run(project_root=tmp_path, patch=True)

    assert result["patched_files"] == []
    assert result["gaps_found"] == 0
