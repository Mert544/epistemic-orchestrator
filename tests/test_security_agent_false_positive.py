from pathlib import Path

from app.agents.skills import SecurityAgent


def test_security_agent_no_false_positive_on_re_compile(tmp_path: Path):
    (tmp_path / "utils.py").write_text(
        "import re\n\ndef parse(text):\n    return re.compile(r'\\d+').match(text)\n",
        encoding="utf-8",
    )
    agent = SecurityAgent()
    result = agent.run(project_root=tmp_path)

    risk_types = {f["risk_type"] for f in result["findings"]}
    assert "compile() usage" not in risk_types


def test_security_agent_no_false_positive_on_literal_eval(tmp_path: Path):
    (tmp_path / "parser.py").write_text(
        "import ast\n\ndef safe_eval(text):\n    return ast.literal_eval(text)\n",
        encoding="utf-8",
    )
    agent = SecurityAgent()
    result = agent.run(project_root=tmp_path)

    risk_types = {f["risk_type"] for f in result["findings"]}
    assert "eval() usage" not in risk_types


def test_security_agent_still_catches_real_eval(tmp_path: Path):
    (tmp_path / "bad.py").write_text(
        "def process(data):\n    return eval(data)\n",
        encoding="utf-8",
    )
    agent = SecurityAgent()
    result = agent.run(project_root=tmp_path)

    risk_types = {f["risk_type"] for f in result["findings"]}
    assert "eval() usage" in risk_types


def test_security_agent_still_catches_real_compile(tmp_path: Path):
    (tmp_path / "bad.py").write_text(
        "def dynamic(code):\n    return compile(code, '<string>', 'exec')\n",
        encoding="utf-8",
    )
    agent = SecurityAgent()
    result = agent.run(project_root=tmp_path)

    risk_types = {f["risk_type"] for f in result["findings"]}
    assert "compile() usage" in risk_types
