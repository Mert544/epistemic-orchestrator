from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class PluginMetadata:
    name: str
    version: str
    description: str
    author: str
    tags: list[str]
    download_url: str


class PluginMarketplace:
    """Client for the Apex Plugin Registry Server.

    Usage:
        market = PluginMarketplace(registry_url="http://localhost:8765")
        plugins = market.list_plugins()
        market.install_plugin("my-plugin", target_dir="./plugins")
    """

    def __init__(self, registry_url: str = "http://localhost:8765") -> None:
        self.registry_url = registry_url.rstrip("/")

    def list_plugins(self) -> list[PluginMetadata]:
        """List available plugins from the registry."""
        req = urllib.request.Request(f"{self.registry_url}/plugins", method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return [
                PluginMetadata(
                    name=p.get("name", ""),
                    version=p.get("version", "0.0.1"),
                    description=p.get("description", ""),
                    author=p.get("author", ""),
                    tags=p.get("tags", []),
                    download_url=p.get("download_url", ""),
                )
                for p in data.get("plugins", [])
            ]

    def get_plugin(self, name: str) -> PluginMetadata | None:
        """Get metadata for a specific plugin."""
        req = urllib.request.Request(f"{self.registry_url}/plugins/{name}", method="GET")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if "error" in data:
                    return None
                return PluginMetadata(
                    name=data.get("name", name),
                    version=data.get("version", "0.0.1"),
                    description=data.get("description", ""),
                    author=data.get("author", ""),
                    tags=data.get("tags", []),
                    download_url=data.get("download_url", ""),
                )
        except Exception:
            return None

    def install_plugin(self, name: str, target_dir: str | Path = "./plugins") -> Path | None:
        """Download and install a plugin to the target directory."""
        target = Path(target_dir)
        target.mkdir(parents=True, exist_ok=True)

        meta = self.get_plugin(name)
        if meta is None:
            return None

        download_url = meta.download_url or f"{self.registry_url}/download/{name}.py"
        req = urllib.request.Request(download_url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                content = resp.read().decode("utf-8")
                plugin_file = target / f"{name}.py"
                plugin_file.write_text(content, encoding="utf-8")
                return plugin_file
        except Exception:
            return None

    def search_plugins(self, query: str) -> list[PluginMetadata]:
        """Search plugins by name or tag."""
        all_plugins = self.list_plugins()
        query_lower = query.lower()
        return [
            p for p in all_plugins
            if query_lower in p.name.lower()
            or any(query_lower in tag.lower() for tag in p.tags)
            or query_lower in p.description.lower()
        ]

    def publish_plugin(
        self,
        plugin_file: str | Path,
        name: str,
        version: str,
        description: str,
        author: str,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Publish a plugin to the registry (requires registry server support).

        Returns the server response.
        """
        path = Path(plugin_file)
        if not path.exists():
            raise FileNotFoundError(f"Plugin file not found: {path}")

        content = path.read_text(encoding="utf-8")
        payload = {
            "name": name,
            "version": version,
            "description": description,
            "author": author,
            "tags": tags or [],
            "content": content,
        }
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.registry_url}/plugins",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
