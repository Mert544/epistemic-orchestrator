from pathlib import Path

from app.agents.skills import DependencyAgent


def _write(root: Path, rel: str, content: str) -> None:
    (root / rel).parent.mkdir(parents=True, exist_ok=True)
    (root / rel).write_text(content, encoding="utf-8")


def test_dependency_agent_builds_import_graph(tmp_path: Path):
    _write(
        tmp_path,
        "app/main.py",
        "from app.services import OrderService\nfrom app.models import User\n\ndef main():\n    pass\n",
    )
    _write(
        tmp_path,
        "app/services.py",
        "from app.models import User\n\ndef create_order():\n    pass\n",
    )
    agent = DependencyAgent()
    result = agent.run(project_root=tmp_path)

    assert result["total_edges"] >= 2
    sources = {e["source"] for e in result["edges"]}
    assert "app/main.py" in sources
    assert "app/services.py" in sources


def test_dependency_agent_detects_orphaned_modules(tmp_path: Path):
    _write(
        tmp_path,
        "app/main.py",
        "from app.services import OrderService\n",
    )
    _write(
        tmp_path,
        "app/services.py",
        "def create_order():\n    pass\n",
    )
    _write(
        tmp_path,
        "app/orphan.py",
        "def unused():\n    pass\n",
    )
    agent = DependencyAgent()
    result = agent.run(project_root=tmp_path)

    assert "app/orphan.py" in result["orphaned_modules"]


def test_dependency_agent_no_circular_imports(tmp_path: Path):
    _write(
        tmp_path,
        "app/a.py",
        "from app.b import b_func\n",
    )
    _write(
        tmp_path,
        "app/b.py",
        "from app.a import a_func\n",
    )
    agent = DependencyAgent()
    result = agent.run(project_root=tmp_path)

    assert len(result["circular_imports"]) >= 1
