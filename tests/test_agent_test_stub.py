from pathlib import Path

from app.agents.skills import TestStubAgent


def _write(root: Path, rel: str, content: str) -> None:
    (root / rel).parent.mkdir(parents=True, exist_ok=True)
    (root / rel).write_text(content, encoding="utf-8")


def test_stub_agent_finds_missing_tests(tmp_path: Path):
    _write(
        tmp_path,
        "app/calc.py",
        "def add(a, b):\n    return a + b\n\ndef sub(a, b):\n    return a - b\n",
    )
    agent = TestStubAgent()
    result = agent.run(project_root=tmp_path)

    assert result["gaps_found"] == 2
    names = {g["symbol_name"] for g in result["gaps"]}
    assert "add" in names
    assert "sub" in names


def test_stub_agent_generates_test_files(tmp_path: Path):
    _write(
        tmp_path,
        "app/calc.py",
        "def add(a, b):\n    return a + b\n",
    )
    agent = TestStubAgent()
    result = agent.run(project_root=tmp_path, generate=True)

    assert len(result["stubs_generated"]) >= 1
    test_file = tmp_path / "tests" / "test_calc.py"
    assert test_file.exists()
    content = test_file.read_text(encoding="utf-8")
    assert "test_add" in content


def test_stub_agent_ignores_private_functions(tmp_path: Path):
    _write(
        tmp_path,
        "app/utils.py",
        "def _internal():\n    pass\n\ndef public():\n    pass\n",
    )
    agent = TestStubAgent()
    result = agent.run(project_root=tmp_path)

    names = {g["symbol_name"] for g in result["gaps"]}
    assert "_internal" not in names
    assert "public" in names
