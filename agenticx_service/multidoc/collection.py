"""Cross-document reduce summarization.

Author: Damon Li
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from agenticx.core.token_counter import count_tokens, truncate_text

from agenticx_service.config import AppConfig
from agenticx_service.core.engine import SummarizationEngine
from agenticx_service.core.types import SummarizeRequest
from agenticx_service.llm_client import LLMClient
from agenticx_service.multidoc.types import (
    CollectionIntent,
    CollectionRequest,
    CollectionResult,
    DocInput,
    PerDocSummary,
)
from agenticx_service.prompts.registry import PromptRegistry

logger = logging.getLogger(__name__)

_INTENT_TEMPLATE = {
    CollectionIntent.AGGREGATE: "collection.aggregate",
    CollectionIntent.COMPARE: "collection.compare",
    CollectionIntent.TIMELINE: "collection.timeline",
}


class CollectionSummarizer:
    """Per-document summarize then cross-document reduce."""

    def __init__(
        self,
        config: AppConfig,
        engine: SummarizationEngine,
        llm_client: LLMClient | None = None,
        prompts: PromptRegistry | None = None,
    ) -> None:
        self.config = config
        self.engine = engine
        self.llm = llm_client or engine.llm
        self.prompts = prompts or engine.prompts

    async def summarize(self, request: CollectionRequest) -> CollectionResult:
        trace: dict[str, Any] = {"per_doc": [], "cross_reduce_rounds": 0}
        semaphore = asyncio.Semaphore(self.config.batch.batch_concurrency)

        async def one(doc: DocInput) -> PerDocSummary:
            async with semaphore:
                req = SummarizeRequest(
                    content=doc.content,
                    domain=doc.domain,
                    parts=doc.parts,
                    options=request.options,
                )
                result = await self.engine.summarize(req)
                summary = await self._maybe_compress(result.text)
                trace["per_doc"].append(
                    {"doc_id": doc.doc_id, "domain": result.domain, "stages": result.trace.get("stages")}
                )
                return PerDocSummary(doc_id=doc.doc_id, title=doc.title, summary=summary)

        per_doc = list(await asyncio.gather(*[one(d) for d in request.docs]))
        cross_input = self._format_cross_input(per_doc)
        template = _INTENT_TEMPLATE[request.intent]
        summary, rounds = await self._cross_reduce(cross_input, template)
        trace["cross_reduce_rounds"] = rounds
        trace["intent"] = request.intent.value
        return CollectionResult(
            summary=summary,
            intent=request.intent,
            per_doc=per_doc,
            trace=trace,
        )

    async def _maybe_compress(self, text: str) -> str:
        max_tokens = self.config.multidoc.per_doc_summary_max_tokens
        tokens = count_tokens(text, model=self.config.llm.model)
        if tokens <= max_tokens:
            return text
        return truncate_text(text, max_tokens=max_tokens, model=self.config.llm.model)

    @staticmethod
    def _format_cross_input(per_doc: list[PerDocSummary]) -> str:
        blocks = []
        for index, doc in enumerate(per_doc, start=1):
            title = doc.title or doc.doc_id
            blocks.append(f"Doc {index}｜{title}\n{doc.summary}")
        return "\n\n".join(blocks)

    async def _cross_reduce(self, numbered: str, template: str) -> tuple[str, int]:
        rounds = 0
        working = numbered
        while True:
            rounds += 1
            tokens = count_tokens(working, model=self.config.llm.model)
            if tokens <= self.config.chunking.max_single_pass_tokens:
                prompt = self.prompts.format(template, partial_summaries=working)
                return await self.llm.complete(prompt), rounds
            midpoint = max(1, len(working.split("\n\n")) // 2)
            parts = working.split("\n\n")
            left = "\n\n".join(parts[:midpoint])
            right = "\n\n".join(parts[midpoint:])
            left_prompt = self.prompts.format(template, partial_summaries=left)
            right_prompt = self.prompts.format(template, partial_summaries=right)
            left_sum = await self.llm.complete(left_prompt)
            right_sum = await self.llm.complete(right_prompt)
            working = f"Doc A merged:\n{left_sum}\n\nDoc B merged:\n{right_sum}"
            if rounds >= self.config.chunking.max_reduce_rounds:
                prompt = self.prompts.format(template, partial_summaries=working)
                return await self.llm.complete(prompt), rounds
