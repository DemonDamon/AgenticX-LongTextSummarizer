"""Deterministic LLM stubs for offline evaluation and tests.

Author: Damon Li
"""

from __future__ import annotations

from typing import Any

from agenticx.llms.response import LLMChoice, LLMResponse, TokenUsage

from agenticx_service.config import AppConfig
from agenticx_service.llm_client import LLMClient


class StubLLMProvider:
    """Deterministic LLM stub."""

    def __init__(self, content: str = "Stub summary output.") -> None:
        self.content = content
        self.calls: list[Any] = []

    async def ainvoke(self, prompt: Any, **kwargs: Any) -> LLMResponse:
        self.calls.append(prompt)
        return LLMResponse(
            id="stub",
            model_name="stub",
            created=0,
            content=self.content,
            choices=[LLMChoice(index=0, content=self.content)],
            token_usage=TokenUsage(),
        )


def make_stub_client(config: AppConfig, content: str = "Stub summary output.") -> LLMClient:
    return LLMClient(config, provider=StubLLMProvider(content=content))
