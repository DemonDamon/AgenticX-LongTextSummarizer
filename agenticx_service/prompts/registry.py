"""Versioned prompt templates for summarization.

Author: Damon Li
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from agenticx.core.prompt import PromptTemplate

_TEMPLATES_PATH = Path(__file__).resolve().parent / "templates.yaml"
_CACHE: dict[str, str] | None = None


def _load_templates() -> dict[str, str]:
    global _CACHE
    if _CACHE is None:
        with _TEMPLATES_PATH.open(encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle) or {}
        _CACHE = {str(key): str(value).strip() for key, value in loaded.items()}
    return _CACHE


class PromptRegistry:
    """Registry of named prompt templates."""

    def __init__(self) -> None:
        self._templates = {
            name: PromptTemplate(template, name=name)
            for name, template in _load_templates().items()
        }

    def get_template(self, name: str) -> PromptTemplate:
        template = self._templates.get(name)
        if template is None:
            raise KeyError(f"Unknown prompt template: {name}")
        return template

    def format(self, name: str, **kwargs: Any) -> str:
        return self.get_template(name).format(**kwargs)


def get_template(name: str) -> str:
    """Return raw template text."""
    templates = _load_templates()
    if name not in templates:
        raise KeyError(f"Unknown prompt template: {name}")
    return templates[name]


def format_prompt(name: str, **kwargs: Any) -> str:
    """Format a named template."""
    return PromptRegistry().format(name, **kwargs)
