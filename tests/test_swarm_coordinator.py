from __future__ import annotations

import pytest

from app.agents.base import Agent, AgentMessage, AgentState
from app.agents.bus import AgentBus
from app.agents.swarm_coordinator import SwarmCoordinator


class FakeSecurityAgent(Agent):
    def __init__(self, bus=None):
        super().__init__(name="security-1", role="security_agent", bus=bus)

    def _execute(self, **kwargs):
        return {"risks": [{"file": "app/auth.py", "issue": "eval() found"}]}


class FakeEvaluatorAgent(Agent):
    def __init__(self, bus=None):
        super().__init__(name="eval-1", role="claim_evaluator", bus=bus)
        self.ran = False

    def _execute(self, **kwargs):
        self.ran = True
        claims = kwargs.get("claims", [])
        return claims


class FakePatcherAgent(Agent):
    def __init__(self, bus=None):
        super().__init__(name="patch-1", role="patch_generator", bus=bus)
        self.ran = False

    def _execute(self, **kwargs):
        self.ran = True
        return {"patched": True}


class TestSwarmCoordinator:
    def test_register_and_wire(self):
        bus = AgentBus()
        coord = SwarmCoordinator(bus=bus)
        sec = FakeSecurityAgent(bus=bus)
        coord.register_agents([sec])
        assert "security-1" in coord.registry.list_instances()

    def test_security_alert_triggers_evaluator(self):
        bus = AgentBus()
        coord = SwarmCoordinator(bus=bus)
        sec = FakeSecurityAgent(bus=bus)
        ev = FakeEvaluatorAgent(bus=bus)
        coord.register_agents([sec, ev])

        # Manually run scan → alert chain
        msg = AgentMessage(sender="test", recipient=None, topic="scan.complete", payload={"project_root": "."})
        coord._handle_scan_complete(sec, msg)

        assert sec.state == AgentState.COMPLETED
        # Coordinator should be subscribed to security.alert
        assert "security.alert" in bus.stats()["topics"]

    def test_run_autonomous_security_goal(self):
        coord = SwarmCoordinator()
        sec = FakeSecurityAgent()
        coord.register_agents([sec])
        results = coord.run_autonomous("security audit", target=".", mode="report")
        assert isinstance(results, list)
        assert coord.stats()["results_count"] >= 0

    def test_stats(self):
        coord = SwarmCoordinator()
        sec = FakeSecurityAgent()
        coord.register_agents([sec])
        stats = coord.stats()
        assert "agents" in stats
        assert "bus" in stats
        assert stats["bus"]["message_count"] >= 0

    def test_shutdown(self):
        coord = SwarmCoordinator()
        coord._running = True
        coord._shutdown()
        assert coord._running is False
