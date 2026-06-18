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
    assert result.trace.get("per_doc")


@pytest.mark.asyncio
async def test_compare_intent_uses_compare_template() -> None:
    config = make_test_config()
    engine = build_engine(config, llm_client=make_stub_client(config))
    summarizer = CollectionSummarizer(config, engine)
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


def test_collection_endpoint_small_sync() -> None:
    config = make_test_config()
    engine = build_engine(config, llm_client=make_stub_client(config))
    client = TestClient(create_app(config=config, engine=engine))
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
