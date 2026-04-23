from __future__ import annotations

"""Agent Registry — discovery, factory, team composition."""

from typing import Any, Callable

from .base import Agent


class AgentRegistry:
    """Registry for agent types and instances.

    Allows dynamic agent creation and team assembly.
    """

    def __init__(self) -> None:
        self._factories: dict[str, Callable[..., Agent]] = {}
        self._instances: dict[str, Agent] = {}

    def register(self, agent_type: str, factory: Callable[..., Agent]) -> None:
        """Register an agent factory by type name."""
        self._factories[agent_type] = factory

    def create(self, agent_type: str, name: str, **kwargs: Any) -> Agent:
        """Create a new agent instance."""
        factory = self._factories.get(agent_type)
        if not factory:
            raise ValueError(f"Unknown agent type: {agent_type}")
        agent = factory(name=name, **kwargs)
        self._instances[name] = agent
        return agent

    def get(self, name: str) -> Agent | None:
        return self._instances.get(name)

    def list_types(self) -> list[str]:
        return list(self._factories.keys())

    def list_instances(self) -> list[str]:
        return list(self._instances.keys())

    def remove(self, name: str) -> None:
        if name in self._instances:
            del self._instances[name]

    def reset_all(self) -> None:
        self._instances.clear()

    def team(self, names: list[str]) -> list[Agent]:
        """Get a team of agents by name."""
        return [self._instances[n] for n in names if n in self._instances]
