from __future__ import annotations

"""Dashboard Server — serves consensus data and HTML dashboard."""

import json
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any

from app.agents.consensus import ConsensusResult


class DashboardHandler(SimpleHTTPRequestHandler):
    """HTTP handler for consensus dashboard."""

    consensus_data: list[dict[str, Any]] = []
    dashboard_html: str = ""

    def do_GET(self) -> None:
        if self.path == "/api/consensus":
            self._send_json(self.consensus_data)
        elif self.path == "/" or self.path == "/dashboard":
            self._send_html(self.dashboard_html)
        else:
            self.send_error(404)

    def _send_json(self, data: Any) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        pass  # Suppress logs


class ConsensusDashboard:
    """Real-time dashboard for monitoring agent consensus."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8766) -> None:
        self.host = host
        self.port = port
        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._load_html()

    def _load_html(self) -> None:
        path = Path(__file__).parent / "dashboard.html"
        if path.exists():
            DashboardHandler.dashboard_html = path.read_text(encoding="utf-8")
        else:
            DashboardHandler.dashboard_html = "<html><body>Dashboard not found</body></html>"

    def update(self, results: list[ConsensusResult]) -> None:
        """Update the dashboard with new consensus results."""
        DashboardHandler.consensus_data = [r.to_dict() for r in results]

    def start(self) -> None:
        """Start the dashboard server in a background thread."""
        if self._server:
            return

        self._server = HTTPServer((self.host, self.port), DashboardHandler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        print(f"Consensus dashboard running at http://{self.host}:{self.port}")

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()
            self._server = None
            self._thread = None

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"
