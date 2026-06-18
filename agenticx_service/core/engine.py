"""Business-agnostic summarization engine.

Author: Damon Li
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from agenticx.core.token_counter import count_tokens

from agenticx_service.chunking import TextChunker
from agenticx_service.config import AppConfig
from agenticx_service.core.prompt_resolver import PromptResolver, StaticPromptResolver
from agenticx_service.core.types import ContentPart, Modality, SummarizeRequest, SummarizeResult
from agenticx_service.domains import build_domain_registry
from agenticx_service.domains.base import DomainRegistry
from agenticx_service.llm_client import LLMClient, PromptInput
from agenticx_service.modality.base import ModalityPipeline
from agenticx_service.overflow import OverflowGuard
from agenticx_service.prompts.registry import PromptRegistry
from agenticx_service.tools.desensitize import mask_pii

logger = logging.getLogger(__name__)


@dataclass
class _CallCost:
    llm_calls: int = 0
    estimated_prompt_tokens: int = 0


class SummarizationEngine:
    """Ingest → guard → route → resolve prompt → LLM → postprocess."""

    def __init__(
        self,
        config: AppConfig,
        llm_client: LLMClient | None = None,
        prompt_registry: PromptRegistry | None = None,
        *,
        domain_registry: DomainRegistry | None = None,
        prompt_resolver: PromptResolver | None = None,
        modality_pipeline: ModalityPipeline | None = None,
    ) -> None:
        self.config = config
        self.llm = llm_client or LLMClient(config)
        self.prompts = prompt_registry or PromptRegistry()
        self.registry = domain_registry or build_domain_registry(config)
        self.resolver = prompt_resolver or StaticPromptResolver(self.registry, self.prompts)
        self.overflow = OverflowGuard(config.overflow, model=config.llm.model)
        self.chunker = TextChunker(config.chunking)
        self.modality = modality_pipeline or ModalityPipeline(config)

    async def _call_llm(self, prompt: PromptInput, cost: _CallCost) -> str:
        if isinstance(prompt, str):
            cost.estimated_prompt_tokens += count_tokens(prompt, model=self.config.llm.model)
        cost.llm_calls += 1
        return await self.llm.complete(prompt)

    async def summarize(self, req: SummarizeRequest) -> SummarizeResult:
        trace: dict[str, Any] = {"stages": [], "modalities": []}
        cost = _CallCost()
        working_text, modality_trace = await self._ingest_text(req)
        trace["modalities"] = modality_trace

        domain_plugin = self.registry.resolve(working_text or req.content, req.domain)
        trace["domain"] = domain_plugin.name
        trace["domain_score"] = domain_plugin.rule_engine.score(working_text or req.content)

        masked = mask_pii(working_text)
        guard = self.overflow.guard_input(masked)
        working = guard.text

        ctx_base: dict[str, Any] = {
            "user_raw_text_input": working,
            "user_id": req.options.get("user_id"),
            "scenario_hint": req.options.get("scenario_hint", ""),
        }

        failed = False
        try:
            if self._should_use_single_pass(working):
                trace["stages"].append("single")
                prompt = await self.resolver.resolve(domain_plugin.name, "single", dict(ctx_base))
                summary = await self._call_llm(prompt, cost)
            else:
                summary, mr_trace = await self._map_reduce(working, domain_plugin.name, ctx_base, cost)
                trace["stages"].extend(mr_trace.get("stages", []))
                trace["chunk_count"] = mr_trace.get("chunk_count", 0)
                trace["reduce_rounds"] = mr_trace.get("reduce_rounds", 0)
        except Exception:  # noqa: BLE001
            logger.exception("Summarization failed")
            summary = self.overflow.failure_message()
            failed = True

        overflow_level = 4 if failed else guard.level

        processed = domain_plugin.postprocess(summary, ctx_base)
        final_text = self.overflow.wrap_result(processed, guard)

        if "_prompt_layers" in ctx_base:
            trace["prompt_layers"] = ctx_base["_prompt_layers"]

        trace["cost"] = {
            "llm_calls": cost.llm_calls,
            "estimated_prompt_tokens": cost.estimated_prompt_tokens,
        }

        return SummarizeResult(
            text=final_text,
            domain=domain_plugin.name,
            overflow_level=overflow_level,
            trace=trace,
        )

    async def _ingest_text(self, req: SummarizeRequest) -> tuple[str, list[str]]:
        parts: list[ContentPart] = list(req.parts or [])
        if req.content:
            parts.insert(0, ContentPart(modality=Modality.TEXT, payload=req.content))
        if not parts:
            return req.content, ["text"]

        sample_text = next(
            (part.payload for part in parts if part.modality == Modality.TEXT),
            req.content,
        )
        domain_plugin = self.registry.resolve(sample_text, req.domain)
        supported = domain_plugin.supported_modalities()
        ctx = {"llm_client": self.llm, "config": self.config}
        return await self.modality.assemble(parts, supported, ctx)

    def _should_use_single_pass(self, text: str) -> bool:
        tokens = count_tokens(text, model=self.config.llm.model)
        return tokens <= self.config.chunking.max_single_pass_tokens

    async def _map_reduce(
        self,
        content: str,
        domain_name: str,
        ctx_base: dict[str, Any],
        cost: _CallCost,
    ) -> tuple[str, dict[str, Any]]:
        trace: dict[str, Any] = {"stages": ["map"]}
        chunks = await self.chunker.split(content)
        if not chunks:
            raise ValueError("Chunking produced no segments")

        if len(chunks) > self.config.overflow.max_chunks:
            chunks = chunks[: self.config.overflow.max_chunks]
            logger.warning(
                "Truncated chunk count to max_chunks=%s",
                self.config.overflow.max_chunks,
            )
        trace["chunk_count"] = len(chunks)

        semaphore = asyncio.Semaphore(self.config.chunking.map_concurrency)

        async def map_chunk(index: int, chunk_text: str) -> str:
            async with semaphore:
                ctx = {**ctx_base, "chunk_index": index + 1, "chunk_text": chunk_text}
                prompt = await self.resolver.resolve(domain_name, "map", ctx)
                return await self._call_llm(prompt, cost)

        partials = list(await asyncio.gather(*[map_chunk(i, c) for i, c in enumerate(chunks)]))
        trace["stages"].append("reduce")
        final, reduce_rounds = await self._reduce_partials(partials, domain_name, ctx_base, 0, cost)
        trace["reduce_rounds"] = reduce_rounds
        return final, trace

    def _format_partials(self, partials: list[str]) -> str:
        return "\n\n".join(
            f"Segment {index + 1}:\n{summary}" for index, summary in enumerate(partials)
        )

    async def _reduce_group(
        self,
        partials: list[str],
        domain_name: str,
        ctx_base: dict[str, Any],
        depth: int,
        cost: _CallCost,
    ) -> str:
        numbered = self._format_partials(partials)
        token_count = count_tokens(numbered, model=self.config.llm.model)
        threshold = self.config.chunking.max_single_pass_tokens
        max_rounds = self.config.chunking.max_reduce_rounds

        if token_count <= threshold or len(partials) <= 1:
            ctx = {**ctx_base, "partial_summaries": numbered}
            prompt = await self.resolver.resolve(domain_name, "reduce", ctx)
            return await self._call_llm(prompt, cost)

        if len(partials) > 1 and depth < max_rounds:
            midpoint = max(1, len(partials) // 2)
            left = await self._reduce_group(partials[:midpoint], domain_name, ctx_base, depth + 1, cost)
            right = await self._reduce_group(partials[midpoint:], domain_name, ctx_base, depth + 1, cost)
            return await self._reduce_group([left, right], domain_name, ctx_base, depth + 1, cost)

        ctx = {**ctx_base, "partial_summaries": numbered}
        prompt = await self.resolver.resolve(domain_name, "reduce", ctx)
        return await self._call_llm(prompt, cost)

    async def _reduce_partials(
        self,
        partials: list[str],
        domain_name: str,
        ctx_base: dict[str, Any],
        depth: int,
        cost: _CallCost,
    ) -> tuple[str, int]:
        if not partials:
            raise ValueError("Reduce received no partial summaries")

        rounds = depth + 1

        if len(partials) == 1:
            result = await self._reduce_group(partials, domain_name, ctx_base, depth, cost)
            return result, rounds

        if depth >= self.config.chunking.max_reduce_rounds:
            result = await self._reduce_group(partials, domain_name, ctx_base, depth, cost)
            return result, rounds

        fan_in = self.config.batch.reduce_fan_in
        groups = [partials[i : i + fan_in] for i in range(0, len(partials), fan_in)]
        semaphore = asyncio.Semaphore(self.config.chunking.map_concurrency)

        async def reduce_one(group: list[str]) -> str:
            async with semaphore:
                return await self._reduce_group(group, domain_name, ctx_base, depth, cost)

        group_results = list(await asyncio.gather(*[reduce_one(g) for g in groups]))

        if len(group_results) == 1:
            return group_results[0], rounds

        final, child_rounds = await self._reduce_partials(
            group_results, domain_name, ctx_base, depth + 1, cost
        )
        return final, max(rounds, child_rounds)
