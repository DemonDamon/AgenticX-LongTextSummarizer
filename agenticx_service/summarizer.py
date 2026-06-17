"""Summarization orchestration service.

Author: Damon Li
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from agenticx.core.token_counter import count_tokens

from agenticx_service.chunking import TextChunker
from agenticx_service.config import AppConfig
from agenticx_service.intent import IntentClassifier
from agenticx_service.llm_client import LLMClient
from agenticx_service.mapreduce import MapReduceSummarizer
from agenticx_service.overflow import OverflowGuard
from agenticx_service.prompts.registry import PromptRegistry
from agenticx_service.tools.desensitize import mask_pii

logger = logging.getLogger(__name__)


@dataclass
class SummarizeResult:
    text: str
    scenario: str = "email"
    overflow_level: int = 1


class SummarizerService:
    """End-to-end summarizer with single-pass and map-reduce paths."""

    def __init__(
        self,
        config: AppConfig,
        llm_client: LLMClient | None = None,
        prompt_registry: PromptRegistry | None = None,
    ) -> None:
        self.config = config
        self.llm = llm_client or LLMClient(config)
        self.prompts = prompt_registry or PromptRegistry()
        self.intent = IntentClassifier(
            config.intent,
            llm_client=self.llm,
            prompt_registry=self.prompts,
        )
        self.overflow = OverflowGuard(config.overflow, model=config.llm.model)
        self.chunker = TextChunker(config.chunking)
        self.map_reduce = MapReduceSummarizer(
            config,
            self.llm,
            self.prompts,
            self.chunker,
        )

    async def summarize(
        self,
        content: str,
        version: str | None = None,
        scenario: str | None = None,
    ) -> SummarizeResult:
        prompt_version = version or self.config.prompts.version
        resolved_scenario = scenario or await self.intent.classify(content) or "email"

        masked = mask_pii(content)
        guard = self.overflow.guard_input(masked)
        working_text = guard.text

        try:
            if self._should_use_single_pass(working_text, prompt_version):
                prompt = self.prompts.format(
                    prompt_version,
                    user_raw_text_input=working_text,
                )
                summary = await self.llm.complete(prompt)
            else:
                summary = await self.map_reduce.run(working_text, resolved_scenario)
        except Exception:  # noqa: BLE001
            logger.exception("Summarization failed")
            summary = self.overflow.failure_message()

        overflow_level = guard.level
        if summary == self.overflow.failure_message():
            overflow_level = 4

        return SummarizeResult(
            text=self.overflow.wrap_result(summary, guard),
            scenario=resolved_scenario,
            overflow_level=overflow_level,
        )

    def _should_use_single_pass(self, text: str, prompt_version: str) -> bool:
        tokens = count_tokens(text, model=self.config.llm.model)
        if tokens > self.config.chunking.max_single_pass_tokens:
            return False
        return prompt_version in {"v1", "v2", "v3", "v4"}
