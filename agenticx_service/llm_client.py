"""LLM client wrapper around AgenticX LlmFactory.

Author: Damon Li
"""

from __future__ import annotations

import logging
from typing import Any, Optional, Union

from agenticx.llms import LlmFactory
from agenticx.llms.base import BaseLLMProvider
from agenticx.llms.response import LLMResponse

from agenticx_service.config import AppConfig

logger = logging.getLogger(__name__)

PromptInput = Union[str, list[dict[str, Any]]]


class LLMClientError(RuntimeError):
    """Raised when an LLM call fails or returns empty content."""


class LLMClient:
    """Thin async wrapper over BaseLLMProvider."""

    def __init__(
        self,
        config: AppConfig,
        provider: Optional[BaseLLMProvider] = None,
    ) -> None:
        self.config = config
        self.llm: BaseLLMProvider = provider or LlmFactory.create_llm(config.to_llm_config())

    async def complete(self, prompt: PromptInput) -> str:
        """Invoke the configured LLM and return text content."""
        try:
            response: LLMResponse = await self.llm.ainvoke(prompt)
        except Exception as exc:  # noqa: BLE001 - surface provider failures
            logger.exception("LLM invocation failed")
            raise LLMClientError(f"LLM invocation failed: {exc}") from exc

        content = (response.content or "").strip()
        if not content and response.choices:
            content = (response.choices[0].content or "").strip()

        if not content:
            raise LLMClientError("LLM returned empty content")

        return content
