"""Cost efficiency and estimate endpoint tests.

Author: Damon Li
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from agenticx_service.app import create_app
from agenticx_service.core.engine import _CallCost
from agenticx_service.core.types import SummarizeRequest
from agenticx_service.factory import build_engine
from agenticx_service.tests.conftest import StubLLMProvider, make_stub_client, make_test_config


@pytest.mark.asyncio
async def test_reduce_fan_in_grouping() -> None:
    """16 map chunks + fan_in=8 reduce: 16 + 2 + 1 = 19 LLM calls."""
    config = make_test_config(
        batch={"reduce_fan_in": 8},
        chunking={
            "max_single_pass_tokens": 500,
            "chunk_size": 100,
            "max_reduce_rounds": 3,
            "map_concurrency": 4,
        },
    )
    provider = StubLLMProvider(content="x")
    client = make_stub_client(config)
    client.llm = provider
    engine = build_engine(config, llm_client=client)
    engine.chunker.split = AsyncMock(return_value=[f"chunk{i}" for i in range(16)])

    long_body = "word " * 500
    await engine.summarize(SummarizeRequest(content=long_body))

    # map: 16 calls; reduce round1: ceil(16/8)=2; reduce round2: 1
    assert len(provider.calls) == 19


@pytest.mark.asyncio
async def test_trace_cost_fields() -> None:
    config = make_test_config(chunking={"max_single_pass_tokens": 10_000})
    engine = build_engine(config, llm_client=make_stub_client(config))
    result = await engine.summarize(SummarizeRequest(content="Short reminder for Friday."))
    cost = result.trace.get("cost")
    assert cost is not None
    assert cost["llm_calls"] >= 1
    assert cost["estimated_prompt_tokens"] > 0


@pytest.mark.asyncio
async def test_reduce_partials_fan_in_only() -> None:
    """Isolate reduce: 16 partials → 3 reduce calls with fan_in=8."""
    config = make_test_config(
        batch={"reduce_fan_in": 8},
        chunking={"max_single_pass_tokens": 100_000, "max_reduce_rounds": 3},
    )
    provider = StubLLMProvider(content="ok")
    client = make_stub_client(config)
    client.llm = provider
    engine = build_engine(config, llm_client=client)
    cost = _CallCost()
    await engine._reduce_partials(
        ["p"] * 16,
        "email",
        {"user_raw_text_input": ""},
        0,
        cost,
    )
    assert cost.llm_calls == 3


def test_estimate_endpoint_inline() -> None:
    config = make_test_config()
    engine = build_engine(config, llm_client=make_stub_client(config))
    with TestClient(create_app(config=config, engine=engine)) as client:
        response = client.post(
            "/v2/estimate",
            json={"items": [{"content": "hello"}]},
        )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["per_item"][0]["calls"] == 1
    assert data["decision"] == "inline"


def test_collection_async_by_calls() -> None:
    config = make_test_config(multidoc={"sync_max_docs": 10, "sync_max_calls": 2})
    engine = build_engine(config, llm_client=make_stub_client(config))
    with TestClient(create_app(config=config, engine=engine)) as client:
        response = client.post(
            "/v2/summarize/collection",
            json={
                "docs": [
                    {"doc_id": str(i), "content": f"Subject: doc {i}"}
                    for i in range(4)
                ],
                "intent": "aggregate",
            },
        )
    assert response.status_code == 202
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["job_id"]
    assert body["data"]["status"] == "queued"
