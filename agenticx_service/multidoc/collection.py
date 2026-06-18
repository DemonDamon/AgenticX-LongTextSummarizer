"""Cross-document reduce summarization.

Author: Damon Li
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from agenticx.core.token_counter import count_tokens, truncate_text

from agenticx_service.config import AppConfig
from agenticx_service.core.engine import SummarizationEngine
from agenticx_service.core.types import SummarizeRequest
from agenticx_service.llm_client import LLMClient, PromptInput
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


@dataclass
class _CallCost:
    llm_calls: int = 0
    estimated_prompt_tokens: int = 0


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

    async def _call_llm(self, prompt: PromptInput, cost: _CallCost) -> str:
        if isinstance(prompt, str):
            cost.estimated_prompt_tokens += count_tokens(prompt, model=self.config.llm.model)
        cost.llm_calls += 1
        return await self.llm.complete(prompt)

    async def summarize(self, request: CollectionRequest) -> CollectionResult:
        trace: dict[str, Any] = {"per_doc": [], "cross_reduce_rounds": 0}
        total_cost = _CallCost()
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
                doc_cost = result.trace.get("cost") or {}
                total_cost.llm_calls += int(doc_cost.get("llm_calls", 0))
                total_cost.estimated_prompt_tokens += int(
                    doc_cost.get("estimated_prompt_tokens", 0)
                )
                summary = await self._maybe_compress(result.text)
                trace["per_doc"].append(
                    {"doc_id": doc.doc_id, "domain": result.domain, "stages": result.trace.get("stages")}
                )
                return PerDocSummary(doc_id=doc.doc_id, title=doc.title, summary=summary)

        per_doc = list(await asyncio.gather(*[one(d) for d in request.docs]))
        cross_input = self._format_cross_input(per_doc)
        template = _INTENT_TEMPLATE[request.intent]
        cross_cost = _CallCost()
        summary, rounds = await self._cross_reduce(cross_input, template, cross_cost)
        total_cost.llm_calls += cross_cost.llm_calls
        total_cost.estimated_prompt_tokens += cross_cost.estimated_prompt_tokens
        trace["cross_reduce_rounds"] = rounds
        trace["intent"] = request.intent.value
        trace["cost"] = {
            "llm_calls": total_cost.llm_calls,
            "estimated_prompt_tokens": total_cost.estimated_prompt_tokens,
        }
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

    async def _cross_reduce(
        self,
        numbered: str,
        template: str,
        cost: _CallCost,
        *,
        depth: int = 0,
    ) -> tuple[str, int]:
        blocks = [b for b in numbered.split("\n\n") if b.strip()]
        if not blocks:
            return "", depth + 1
        result, rounds = await self._cross_reduce_blocks(blocks, template, cost, depth)
        return result, rounds

    async def _cross_reduce_blocks(
        self,
        blocks: list[str],
        template: str,
        cost: _CallCost,
        depth: int,
    ) -> tuple[str, int]:
        rounds = depth + 1

        if len(blocks) == 1:
            working = blocks[0]
            prompt = self.prompts.format(template, partial_summaries=working)
            return await self._call_llm(prompt, cost), rounds

        if depth >= self.config.chunking.max_reduce_rounds:
            working = "\n\n".join(blocks)
            prompt = self.prompts.format(template, partial_summaries=working)
            return await self._call_llm(prompt, cost), rounds

        fan_in = self.config.batch.reduce_fan_in
        groups = [blocks[i : i + fan_in] for i in range(0, len(blocks), fan_in)]
        semaphore = asyncio.Semaphore(self.config.chunking.map_concurrency)

        async def reduce_group(group: list[str]) -> str:
            async with semaphore:
                return await self._cross_reduce_group(group, template, cost, depth)

        group_results = list(await asyncio.gather(*[reduce_group(g) for g in groups]))

        if len(group_results) == 1:
            return group_results[0], rounds

        return await self._cross_reduce_blocks(group_results, template, cost, depth + 1)

    async def _cross_reduce_group(
        self,
        blocks: list[str],
        template: str,
        cost: _CallCost,
        depth: int,
    ) -> str:
        working = "\n\n".join(blocks)
        tokens = count_tokens(working, model=self.config.llm.model)
        threshold = self.config.chunking.max_single_pass_tokens
        max_rounds = self.config.chunking.max_reduce_rounds

        if tokens <= threshold or len(blocks) <= 1:
            prompt = self.prompts.format(template, partial_summaries=working)
            return await self._call_llm(prompt, cost)

        if len(blocks) > 1 and depth < max_rounds:
            midpoint = max(1, len(blocks) // 2)
            left = await self._cross_reduce_group(blocks[:midpoint], template, cost, depth + 1)
            right = await self._cross_reduce_group(blocks[midpoint:], template, cost, depth + 1)
            merged = f"Doc A merged:\n{left}\n\nDoc B merged:\n{right}"
            prompt = self.prompts.format(template, partial_summaries=merged)
            return await self._call_llm(prompt, cost)

        prompt = self.prompts.format(template, partial_summaries=working)
        return await self._call_llm(prompt, cost)
