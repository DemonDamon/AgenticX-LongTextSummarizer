"""Domain plugin protocol and registry.

Author: Damon Li
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from agenticx_service.core.types import Modality


@runtime_checkable
class RuleEngine(Protocol):
    def score(self, content: str) -> float:
        ...


@runtime_checkable
class DomainPlugin(Protocol):
    name: str
    rule_engine: RuleEngine

    def prompt_ids(self) -> dict[str, str]:
        ...

    def supported_modalities(self) -> set[Modality]:
        ...

    def postprocess(self, summary: str, ctx: dict) -> str:
        ...


class DomainRegistry:
    """Register domain plugins and resolve the best match for content."""

    def __init__(self, plugins: list[DomainPlugin], *, default_domain: str = "email") -> None:
        self._plugins = {plugin.name: plugin for plugin in plugins}
        self.default_domain = default_domain

    def register(self, plugin: DomainPlugin) -> None:
        self._plugins[plugin.name] = plugin

    def get(self, name: str) -> DomainPlugin:
        if name not in self._plugins:
            raise KeyError(f"Unknown domain: {name}")
        return self._plugins[name]

    def all_plugins(self) -> list[DomainPlugin]:
        return list(self._plugins.values())

    def resolve(self, content: str, explicit: str | None = None) -> DomainPlugin:
        if explicit:
            return self.get(explicit)
        best: DomainPlugin | None = None
        best_score = 0.0
        for plugin in self._plugins.values():
            score = plugin.rule_engine.score(content)
            if score > best_score:
                best_score = score
                best = plugin
        if best is None or best_score <= 0.0:
            return self.get(self.default_domain)
        return best
