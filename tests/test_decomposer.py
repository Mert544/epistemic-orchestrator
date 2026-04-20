from pathlib import Path

from app.skills.decomposer import Decomposer


def test_project_aware_decomposer_seeds_structural_claims(tmp_path: Path):
    (tmp_path / "app").mkdir()
    (tmp_path / "auth").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "workflows").mkdir(parents=True, exist_ok=True)

    (tmp_path / "app" / "main.py").write_text(
        "import os\nfrom auth.token_service import TokenService\n\nclass App:\n    pass\n\ndef run():\n    return True\n",
        encoding="utf-8",
    )
    (tmp_path / "auth" / "token_service.py").write_text(
        "import secrets\n\nclass TokenService:\n    pass\n\ndef issue_token():\n    return secrets.token_hex()\n",
        encoding="utf-8",
    )
    (tmp_path / "tests" / "test_main.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    (tmp_path / ".github" / "workflows" / "ci.yml").write_text("name: ci\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")

    decomposer = Decomposer(project_root=tmp_path)
    claims = decomposer.decompose(
        "Scan the target project, extract meaningful implementation claims, and continue with constitution-driven fractal questioning."
    )

    assert len(claims) >= 7
    assert any("Project profile claim" in claim for claim in claims)
    assert any("Entrypoint claim" in claim for claim in claims)
    assert any("Dependency hub claim" in claim for claim in claims)
    assert any("Symbol density claim" in claim for claim in claims)
    assert any("Untested module claim" in claim for claim in claims)
    assert any("Automation claim" in claim for claim in claims)


def test_decomposer_normalizes_question_child_claim_without_fragmenting_paths():
    decomposer = Decomposer()
    claims = decomposer.decompose(
        "What critical information is missing to validate this claim: Dependency hub claim: the files app/services/order_service.py, app/payments/gateway.py, appear central in the import graph and should be expanded first for dependency risk and architectural coupling?"
    )

    assert len(claims) == 1
    assert claims[0].startswith("Missing-information claim:")
    assert "app/services/order_service.py" in claims[0]
    assert "app/payments/gateway.py" in claims[0]
    assert "What critical information" not in claims[0]
