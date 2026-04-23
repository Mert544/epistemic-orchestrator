from app.agents.base import Agent, AgentMessage, AgentState
from app.agents.bus import AgentBus


def test_agent_lifecycle():
    agent = Agent(name="test", role="tester")
    assert agent.state == AgentState.IDLE

    result = agent.run()
    assert agent.state == AgentState.FAILED  # _execute not implemented

    agent.reset()
    assert agent.state == AgentState.IDLE
    assert agent.inbox == []


def test_agent_messaging():
    bus = AgentBus()
    a1 = Agent(name="alice", role="sender", bus=bus)
    a2 = Agent(name="bob", role="receiver", bus=bus)

    received = []
    a2.on("test.topic", lambda msg: received.append(msg.payload))

    a1.send("test.topic", {"hello": "world"}, recipient="bob")
    assert len(received) == 1
    assert received[0]["hello"] == "world"


def test_agent_broadcast():
    bus = AgentBus()
    a1 = Agent(name="alice", role="test", bus=bus)
    a2 = Agent(name="bob", role="test", bus=bus)
    a3 = Agent(name="charlie", role="test", bus=bus)

    received = []
    a2.on("broadcast", lambda msg: received.append(msg.sender))
    a3.on("broadcast", lambda msg: received.append(msg.sender))

    bus.broadcast("alice", "broadcast", {"msg": "hi"})
    assert len(received) == 2


def test_bus_history():
    bus = AgentBus()
    bus.broadcast("a", "topic1", {"x": 1})
    bus.broadcast("b", "topic2", {"x": 2})
    bus.broadcast("c", "topic1", {"x": 3})

    history = bus.get_history(topic="topic1")
    assert len(history) == 2

    history = bus.get_history(sender="b")
    assert len(history) == 1


def test_agent_team_sequential():
    from app.agents.team import AgentTeam

    class AddAgent(Agent):
        def __init__(self, name: str, **kwargs):
            super().__init__(name=name, role="adder", **kwargs)

        def _execute(self, value: int = 0, **kwargs):
            return {"value": value + 1}

    team = AgentTeam(name="incrementers")
    team.add(AddAgent(name="a1"))
    team.add(AddAgent(name="a2"))

    result = team.run_sequential(value=0)
    assert result.agent_results["a1"]["value"] == 1
    assert result.agent_results["a2"]["value"] == 2


def test_agent_team_parallel():
    from app.agents.team import AgentTeam

    class ConstAgent(Agent):
        def __init__(self, name: str, **kwargs):
            super().__init__(name=name, role="const", **kwargs)

        def _execute(self, **kwargs):
            return {"result": self.name}

    team = AgentTeam(name="parallel")
    team.add(ConstAgent(name="x"))
    team.add(ConstAgent(name="y"))

    result = team.run_parallel()
    assert result.agent_results["x"]["result"] == "x"
    assert result.agent_results["y"]["result"] == "y"


def test_agent_registry():
    from app.agents.registry import AgentRegistry

    registry = AgentRegistry()
    registry.register("const", lambda name: Agent(name=name, role="test"))

    agent = registry.create("const", "my_agent")
    assert agent.name == "my_agent"
    assert registry.get("my_agent") is agent
    assert "const" in registry.list_types()


def test_team_pipeline():
    from app.agents.team import AgentTeam

    class Stage1Agent(Agent):
        def __init__(self, name: str, **kwargs):
            super().__init__(name=name, role="stage", **kwargs)

        def _execute(self, data: str = "", **kwargs):
            return {"data": data + "A"}

    class Stage2Agent(Agent):
        def __init__(self, name: str, **kwargs):
            super().__init__(name=name, role="stage", **kwargs)

        def _execute(self, data: str = "", **kwargs):
            return {"data": data + "B"}

    team = AgentTeam(name="pipeline")
    team.add(Stage1Agent(name="stage1"))
    team.add(Stage2Agent(name="stage2"))

    result = team.run_pipeline(stages=[["stage1"], ["stage2"]], data="")
    assert result.agent_results["stage2"]["data"] == "AB"
