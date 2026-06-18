"""Phase D multi-document summarization smoke tests.

Author: Damon Li
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from agenticx_service.app import create_app
from agenticx_service.multidoc.collection import CollectionSummarizer
from agenticx_service.multidoc.types import CollectionIntent, CollectionRequest, DocInput
from agenticx_service.factory import build_engine
from agenticx_service.tests.conftest import make_stub_client, make_test_config


@pytest.mark.asyncio
async def test_aggregate_two_docs() -> None:
    config = make_test_config()
    engine = build_engine(config, llm_client=make_stub_client(config))
    summarizer = CollectionSummarizer(config, engine)
    request = CollectionRequest(
        docs=[
            DocInput(doc_id="d1", title="A", content="Subject: plan A"),
            DocInput(doc_id="d2", title="B", content="Subject: plan B"),
        ],
        intent=CollectionIntent.AGGREGATE,
    )
    result = await summarizer.summarize(request)
    assert result.summary
    assert len(result.per_doc) == 2
    assert len(result.trace.get("per_doc", [])) == 2
    assert result.trace.get("cross_reduce_rounds", 0) >= 1


@pytest.mark.asyncio
async def test_compare_intent_uses_compare_template(monkeypatch: pytest.MonkeyPatch) -> None:
    config = make_test_config()
    engine = build_engine(config, llm_client=make_stub_client(config))
    summarizer = CollectionSummarizer(config, engine)
    used_templates: list[str] = []
    original_format = summarizer.prompts.format

    def track_format(template_id: str, **kwargs: object) -> str:
        used_templates.append(template_id)
        return original_format(template_id, **kwargs)

    monkeypatch.setattr(summarizer.prompts, "format", track_format)
    request = CollectionRequest(
        docs=[
            DocInput(doc_id="d1", content="记者报道 A"),
            DocInput(doc_id="d2", content="记者报道 B"),
        ],
        intent=CollectionIntent.COMPARE,
    )
    result = await summarizer.summarize(request)
    assert result.intent == CollectionIntent.COMPARE
    assert result.summary
    assert "collection.compare" in used_templates


@pytest.mark.asyncio
async def test_timeline_intent_orders_events(monkeypatch: pytest.MonkeyPatch) -> None:
    config = make_test_config()
    engine = build_engine(config, llm_client=make_stub_client(config))
    summarizer = CollectionSummarizer(config, engine)
    used_templates: list[str] = []
    original_format = summarizer.prompts.format

    def track_format(template_id: str, **kwargs: object) -> str:
        used_templates.append(template_id)
        return original_format(template_id, **kwargs)

    monkeypatch.setattr(summarizer.prompts, "format", track_format)
    request = CollectionRequest(
        docs=[
            DocInput(doc_id="d1", title="Jan", content="2024-01-01 kickoff"),
            DocInput(doc_id="d2", title="Mar", content="2024-03-01 milestone"),
        ],
        intent=CollectionIntent.TIMELINE,
    )
    result = await summarizer.summarize(request)
    assert result.intent == CollectionIntent.TIMELINE
    assert result.trace.get("intent") == "timeline"
    assert "collection.timeline" in used_templates


@pytest.mark.asyncio
async def test_large_collection_multi_level_reduce() -> None:
    long_summary = "event " * 800
    config = make_test_config(
        chunking={"max_single_pass_tokens": 30, "max_reduce_rounds": 5},
        batch={"reduce_fan_in": 2},
    )
    engine = build_engine(config, llm_client=make_stub_client(config, content=long_summary))
    summarizer = CollectionSummarizer(config, engine)
    request = CollectionRequest(
        docs=[
            DocInput(doc_id=f"d{i}", title=f"Doc{i}", content=f"Subject: doc {i}")
            for i in range(1, 5)
        ],
        intent=CollectionIntent.AGGREGATE,
    )
    result = await summarizer.summarize(request)
    assert result.summary
    assert result.trace.get("cross_reduce_rounds", 0) > 1


def test_collection_endpoint_small_sync() -> None:
    config = make_test_config()
    engine = build_engine(config, llm_client=make_stub_client(config))
    with TestClient(create_app(config=config, engine=engine)) as client:
        response = client.post(
            "/v2/summarize/collection",
            json={
                "docs": [
                    {"doc_id": "1", "content": "Subject: one"},
                    {"doc_id": "2", "content": "Subject: two"},
                ],
                "intent": "aggregate",
            },
        )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["summary"]
    assert len(data["per_doc"]) == 2
    assert data["trace"]


def test_collection_endpoint_large_enqueue() -> None:
    config = make_test_config(multidoc={"sync_max_docs": 1})
    engine = build_engine(config, llm_client=make_stub_client(config))
    with TestClient(create_app(config=config, engine=engine)) as client:
        response = client.post(
            "/v2/summarize/collection",
            json={
                "docs": [
                    {"doc_id": "1", "content": "Subject: one"},
                    {"doc_id": "2", "content": "Subject: two"},
                ],
                "intent": "aggregate",
            },
        )
    assert response.status_code == 202
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["job_id"]
    assert body["data"]["status"] == "queued"
