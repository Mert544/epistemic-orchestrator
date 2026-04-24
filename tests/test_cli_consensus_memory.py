from pathlib import Path

from app.cli import cmd_consensus
import argparse


def test_consensus_cli_without_memory(tmp_path: Path, monkeypatch):
    args = argparse.Namespace(
        claims="Add docstrings;Use eval() for config",
        strategy="majority",
        quorum=2,
        json=False,
        use_memory=False,
        target=str(tmp_path),
    )
    result = cmd_consensus(args)
    assert result == 0


def test_consensus_cli_with_memory(tmp_path: Path, monkeypatch):
    # Mock memory dir to tmp
    monkeypatch.setattr("app.cli._get_project_root", lambda: tmp_path)
    args = argparse.Namespace(
        claims="Add docstrings;Use eval() for config",
        strategy="majority",
        quorum=2,
        json=False,
        use_memory=True,
        target=str(tmp_path),
    )
    result = cmd_consensus(args)
    assert result == 0
