"""Summarization orchestration service (v1 adapter over v2 engine).

Author: Damon Li
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from agenticx_service.config import AppConfig
from agenticx_service.core.types import SummarizeRequest
from agenticx_service.factory import build_engine
from agenticx_service.llm_client import LLMClient
from agenticx_service.prompts.registry import PromptRegistry

logger = logging.getLogger(__name__)


@dataclass
class SummarizeResult:
    text: str
    scenario: str = "email"
    overflow_level: int = 1


class SummarizerService:
    """End-to-end summarizer delegating to SummarizationEngine."""

    def __init__(
        self,
        config: AppConfig,
        llm_client: LLMClient | None = None,
        prompt_registry: PromptRegistry | None = None,
    ) -> None:
        self.config = config
        self.llm = llm_client or LLMClient(config)
        self.prompts = prompt_registry or PromptRegistry()
        self.engine = build_engine(config, llm_client=self.llm, prompt_registry=self.prompts)

    async def summarize(
        self,
        content: str,
        version: str | None = None,
        scenario: str | None = None,
    ) -> SummarizeResult:
        req = SummarizeRequest(
            content=content,
            domain=scenario,
            options={"prompt_version": version or self.config.prompts.version},
        )
        result = await self.engine.summarize(req)
        return SummarizeResult(
            text=result.text,
            scenario=result.domain,
            overflow_level=result.overflow_level,
        )
