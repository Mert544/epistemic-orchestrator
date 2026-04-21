from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.automation.models import AutomationContext


SkillCallable = Callable[[AutomationContext], Any]


class SkillAutomationRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, SkillCallable] = {}

    def register(self, name: str, skill: SkillCallable) -> None:
        self._skills[name] = skill

    def get(self, name: str) -> SkillCallable:
        if name not in self._skills:
            raise KeyError(f"Unknown automation skill: {name}")
        return self._skills[name]

    def has(self, name: str) -> bool:
        return name in self._skills

    def list_names(self) -> list[str]:
        return sorted(self._skills.keys())
