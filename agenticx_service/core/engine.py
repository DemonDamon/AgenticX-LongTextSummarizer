"""Business-agnostic summarization engine.

Author: Damon Li
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from agenticx.core.token_counter import count_tokens

from agenticx_service.chunking import TextChunker
from agenticx_service.config import AppConfig
from agenticx_service.core.prompt_resolver import PromptResolver, StaticPromptResolver
from agenticx_service.core.types import ContentPart, Modality, SummarizeRequest, SummarizeResult
from agenticx_service.domains import build_domain_registry
from agenticx_service.domains.base import DomainRegistry
from agenticx_service.llm_client import LLMClient
from agenticx_service.modality.base import ModalityPipeline
from agenticx_service.overflow import OverflowGuard
from agenticx_service.prompts.registry import PromptRegistry
from agenticx_service.tools.desensitize import mask_pii

logger = logging.getLogger(__name__)


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

    async def summarize(self, req: SummarizeRequest) -> SummarizeResult:
        trace: dict[str, Any] = {"stages": [], "modalities": []}
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
                summary = await self.llm.complete(prompt)
            else:
                summary, mr_trace = await self._map_reduce(working, domain_plugin.name, ctx_base)
                trace["stages"].extend(mr_trace.get("stages", []))
                trace["chunk_count"] = mr_trace.get("chunk_count", 0)
        except Exception:  # noqa: BLE001
            logger.exception("Summarization failed")
            summary = self.overflow.failure_message()
            failed = True

        overflow_level = 4 if failed else guard.level

        processed = domain_plugin.postprocess(summary, ctx_base)
        final_text = self.overflow.wrap_result(processed, guard)

        if "_prompt_layers" in ctx_base:
            trace["prompt_layers"] = ctx_base["_prompt_layers"]

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
                return await self.llm.complete(prompt)

        partials = list(await asyncio.gather(*[map_chunk(i, c) for i, c in enumerate(chunks)]))
        trace["stages"].append("reduce")
        final = await self._reduce_partials(partials, domain_name, ctx_base, depth=0)
        return final, trace

    async def _reduce_partials(
        self,
        partials: list[str],
        domain_name: str,
        ctx_base: dict[str, Any],
        depth: int,
    ) -> str:
        numbered = "\n\n".join(
            f"Segment {index + 1}:\n{summary}" for index, summary in enumerate(partials)
        )
        ctx = {**ctx_base, "partial_summaries": numbered}
        prompt = await self.resolver.resolve(domain_name, "reduce", ctx)

        token_count = count_tokens(numbered, model=self.config.llm.model)
        if (
            token_count > self.config.chunking.max_single_pass_tokens
            and len(partials) > 1
            and depth < self.config.chunking.max_reduce_rounds
        ):
            midpoint = max(1, len(partials) // 2)
            left = await self._reduce_partials(partials[:midpoint], domain_name, ctx_base, depth + 1)
            right = await self._reduce_partials(partials[midpoint:], domain_name, ctx_base, depth + 1)
            return await self._reduce_partials([left, right], domain_name, ctx_base, depth + 1)

        return await self.llm.complete(prompt)
