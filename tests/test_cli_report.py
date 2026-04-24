from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.cli import cmd_report
import argparse


def test_report_markdown(tmp_path: Path):
    data = {"swarm_results": [{"agent": "security", "findings": [{"issue": "eval", "severity": "critical", "file": "a.py"}]}]}
    inp = tmp_path / "run.json"
    inp.write_text(json.dumps(data))
    out = tmp_path / "report.md"
    args = argparse.Namespace(input=str(inp), format="markdown", output=str(out))
    assert cmd_report(args) == 0
    assert out.exists()
    assert "eval" in out.read_text()


def test_report_html(tmp_path: Path):
    data = {"results": [{"agent": "sec", "findings": []}]}
    inp = tmp_path / "run.json"
    inp.write_text(json.dumps(data))
    out = tmp_path / "report.html"
    args = argparse.Namespace(input=str(inp), format="html", output=str(out))
    assert cmd_report(args) == 0
    assert "No findings" in out.read_text()


def test_report_missing_input(tmp_path: Path):
    args = argparse.Namespace(input=str(tmp_path / "missing.json"), format="markdown", output=str(tmp_path / "out.md"))
    assert cmd_report(args) == 1
