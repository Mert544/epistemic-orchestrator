from __future__ import annotations

import time
import urllib.request

import pytest

from app.engine.distributed_swarm import (
    DistributedSwarmCoordinator,
    DistributedSwarmResult,
    SwarmNode,
    SwarmNodeServer,
)


def test_swarm_node_url():
    node = SwarmNode("node-1", "127.0.0.1", 18765)
    assert node.url("/health") == "http://127.0.0.1:18765/health"
    assert node.url() == "http://127.0.0.1:18765"


def test_distributed_result_to_dict():
    r = DistributedSwarmResult(
        aggregated_output={"k": "v"}, errors=["e"], nodes_completed=1, nodes_failed=0
    )
    d = r.to_dict()
    assert d["nodes_completed"] == 1
    assert d["errors"] == ["e"]


def test_coordinator_no_online_nodes():
    coord = DistributedSwarmCoordinator([SwarmNode("n1", "127.0.0.1", 59999)])
    result = coord.run("scan", [{"item": 1}])
    assert result.nodes_completed == 0
    assert len(result.errors) == 1
    assert "No online nodes" in result.errors[0]


class TestSwarmNodeServer:
    @pytest.fixture(scope="module")
    def swarm_server(self):
        server = SwarmNodeServer("test-node", host="127.0.0.1", port=18766)
        server.register_task("echo", lambda p: {"received": p})
        import threading
        t = threading.Thread(target=server.start, daemon=True)
        t.start()
        time.sleep(0.3)
        yield server
        server.stop()

    def test_node_server_health(self, swarm_server):
        req = urllib.request.Request("http://127.0.0.1:18766/health", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = resp.read().decode("utf-8")
            import json
            assert json.loads(data)["status"] == "ok"
            assert json.loads(data)["node_id"] == "test-node"

    def test_node_server_execute(self, swarm_server):
        import json
        body = json.dumps({"task": "echo", "payload": {"x": 42}}).encode("utf-8")
        req = urllib.request.Request(
            "http://127.0.0.1:18766/execute",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            assert data["node_id"] == "test-node"
            assert data["result"]["received"]["x"] == 42

    def test_node_server_unknown_task(self, swarm_server):
        import json
        body = json.dumps({"task": "nope", "payload": {}}).encode("utf-8")
        req = urllib.request.Request(
            "http://127.0.0.1:18766/execute",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            assert "Unknown task" in data["error"]

    def test_distributed_run_e2e(self, swarm_server):
        coord = DistributedSwarmCoordinator([SwarmNode("test-node", "127.0.0.1", 18766)])
        result = coord.run("echo", [{"x": 1}, {"x": 2}])
        assert result.nodes_completed == 2
        assert result.nodes_failed == 0
        assert len(result.aggregated_output["responses"]) == 2
