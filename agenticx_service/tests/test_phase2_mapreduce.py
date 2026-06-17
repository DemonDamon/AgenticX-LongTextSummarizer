"""Phase 2 map-reduce tests.

Author: Damon Li
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from agenticx_service.chunking import TextChunker
from agenticx_service.mapreduce import MapReduceSummarizer
from agenticx_service.prompts.registry import PromptRegistry
from agenticx_service.summarizer import SummarizerService
from agenticx_service.tests.conftest import StubLLMProvider, make_stub_client, make_test_config


@pytest.mark.asyncio
async def test_short_text_uses_single_pass() -> None:
    config = make_test_config(chunking={"max_single_pass_tokens": 10_000})
    service = SummarizerService(config, llm_client=make_stub_client(config))
    service.map_reduce.run = AsyncMock()  # type: ignore[method-assign]

    await service.summarize("Short meeting reminder for Friday.")

    service.map_reduce.run.assert_not_called()


@pytest.mark.asyncio
async def test_long_text_triggers_mapreduce() -> None:
    config = make_test_config(chunking={"max_single_pass_tokens": 20, "chunk_size": 200})
    long_text = "Paragraph about billing migration. " * 400
    provider = StubLLMProvider(content="Partial summary")
    client = make_stub_client(config)
    client.llm = provider
    service = SummarizerService(config, llm_client=client)

    result = await service.summarize(long_text)
    assert result.text
    assert len(provider.calls) > 1


@pytest.mark.asyncio
async def test_lost_in_middle_map_calls_multiple_chunks() -> None:
    config = make_test_config(
        chunking={
            "max_single_pass_tokens": 20,
            "chunk_size": 120,
            "chunk_overlap": 0,
            "map_concurrency": 2,
        }
    )
    start = "ANCHOR_START: Should we migrate billing this quarter?"
    end = "ANCHOR_END: Final decision is phased rollout in Q3."
    body = "Discussion paragraph. " * 80
    text = f"{start}\n{body}\n{end}"

    provider = StubLLMProvider(content="chunk summary")
    client = make_stub_client(config)
    client.llm = provider
    service = SummarizerService(config, llm_client=client)

    await service.summarize(text)
    assert len(provider.calls) >= 2


@pytest.mark.asyncio
async def test_mapreduce_respects_concurrency() -> None:
    config = make_test_config(
        chunking={
            "chunk_size": 50,
            "chunk_overlap": 0,
            "map_concurrency": 1,
            "max_reduce_rounds": 2,
        }
    )
    client = make_stub_client(config)
    summarizer = MapReduceSummarizer(
        config,
        client,
        PromptRegistry(),
        TextChunker(config.chunking),
    )
    text = "A" * 1000
    result = await summarizer.run(text, "email")
    assert result
