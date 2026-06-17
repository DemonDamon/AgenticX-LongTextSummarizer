"""Map-Reduce summarization engine.

Author: Damon Li
"""

from __future__ import annotations

import asyncio
import logging
from typing import List

from agenticx.core.token_counter import count_tokens

from agenticx_service.chunking import TextChunker
from agenticx_service.config import AppConfig
from agenticx_service.llm_client import LLMClient
from agenticx_service.prompts.registry import PromptRegistry

logger = logging.getLogger(__name__)


class MapReduceSummarizer:
    """Chunk, map partial summaries, and reduce to a final answer."""

    def __init__(
        self,
        config: AppConfig,
        llm_client: LLMClient,
        prompt_registry: PromptRegistry,
        chunker: TextChunker,
    ) -> None:
        self.config = config
        self.llm = llm_client
        self.prompts = prompt_registry
        self.chunker = chunker

    async def run(self, content: str, scenario: str) -> str:
        chunks = await self.chunker.split(content)
        if not chunks:
            raise ValueError("Chunking produced no segments")

        if len(chunks) > self.config.overflow.max_chunks:
            chunks = chunks[: self.config.overflow.max_chunks]
            logger.warning(
                "Truncated chunk count to max_chunks=%s",
                self.config.overflow.max_chunks,
            )

        partials = await self._map_phase(chunks, scenario)
        return await self._reduce_phase(partials, scenario, depth=0)

    async def _map_phase(self, chunks: List[str], scenario: str) -> List[str]:
        semaphore = asyncio.Semaphore(self.config.chunking.map_concurrency)
        map_template = f"map_{scenario}"

        async def summarize_chunk(index: int, chunk_text: str) -> str:
            async with semaphore:
                prompt = self.prompts.format(
                    map_template,
                    chunk_index=index + 1,
                    chunk_text=chunk_text,
                )
                return await self.llm.complete(prompt)

        tasks = [summarize_chunk(index, chunk) for index, chunk in enumerate(chunks)]
        return list(await asyncio.gather(*tasks))

    async def _reduce_phase(
        self,
        partials: List[str],
        scenario: str,
        depth: int,
    ) -> str:
        numbered = "\n\n".join(
            f"Segment {index + 1}:\n{summary}"
            for index, summary in enumerate(partials)
        )
        reduce_template = f"reduce_{scenario}"
        prompt = self.prompts.format(
            reduce_template,
            partial_summaries=numbered,
        )

        token_count = count_tokens(numbered, model=self.config.llm.model)
        if (
            token_count > self.config.chunking.max_single_pass_tokens
            and len(partials) > 1
            and depth < self.config.chunking.max_reduce_rounds
        ):
            midpoint = max(1, len(partials) // 2)
            left = await self._reduce_phase(partials[:midpoint], scenario, depth + 1)
            right = await self._reduce_phase(partials[midpoint:], scenario, depth + 1)
            return await self._reduce_phase([left, right], scenario, depth + 1)

        return await self.llm.complete(prompt)
