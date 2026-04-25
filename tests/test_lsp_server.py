from __future__ import annotations

from app.lsp.server import LSPServer


def test_lsp_analyze_eval():
    server = LSPServer()
    diagnostics = server._analyze("file:///test.py", "def f(x):\n    return eval(x)\n")
    assert len(diagnostics) >= 1
    assert any("eval()" in d["message"] for d in diagnostics)


def test_lsp_analyze_bare_except():
    server = LSPServer()
    diagnostics = server._analyze("file:///test.py", "try:\n    pass\nexcept:\n    pass\n")
    assert any("bare except" in d["message"] for d in diagnostics)


def test_lsp_analyze_missing_docstring():
    server = LSPServer()
    diagnostics = server._analyze("file:///test.py", "def hello():\n    pass\n")
    assert any("missing docstring" in d["message"] for d in diagnostics)


def test_lsp_hover_info():
    server = LSPServer()
    info = server._get_hover_info("eval")
    assert "eval()" in info


def test_lsp_extract_symbols():
    server = LSPServer()
    symbols = server._extract_symbols("def foo():\n    pass\nclass Bar:\n    pass\n")
    assert len(symbols) == 2
    assert symbols[0]["name"] == "foo"
    assert symbols[1]["name"] == "Bar"
