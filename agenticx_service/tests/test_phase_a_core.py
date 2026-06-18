"""Phase A core/domain decoupling smoke tests.

Author: Damon Li
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agenticx_service.app import create_app
from agenticx_service.config import AppConfig
from agenticx_service.core.engine import SummarizationEngine
from agenticx_service.core.types import SummarizeRequest
from agenticx_service.domains import build_domain_registry
from agenticx_service.factory import build_engine
from agenticx_service.tests.conftest import make_stub_client, make_test_config


@pytest.mark.asyncio
async def test_domain_registry_routes_email_vs_news() -> None:
    config = make_test_config()
    registry = build_domain_registry(config)
    email_plugin = registry.resolve("Subject: meeting\nPlease confirm.", None)
    news_plugin = registry.resolve("本报讯 记者报道 据悉", None)
    assert email_plugin.name == "email"
    assert news_plugin.name == "news"


@pytest.mark.asyncio
async def test_engine_single_pass_email() -> None:
    config = make_test_config()
    engine = build_engine(config, llm_client=make_stub_client(config))
    result = await engine.summarize(
        SummarizeRequest(content="Subject: Sync\nPlease confirm Friday attendance.")
    )
    assert result.text
    assert result.domain == "email"
    assert "single" in result.trace.get("stages", [])


@pytest.mark.asyncio
async def test_engine_mapreduce_routes_by_tokens() -> None:
    config = make_test_config(chunking={"max_single_pass_tokens": 10, "chunk_size": 50})
    engine = build_engine(config, llm_client=make_stub_client(config))
    long_text = "word " * 500
    result = await engine.summarize(SummarizeRequest(content=long_text, domain="email"))
    stages = result.trace.get("stages", [])
    assert "map" in stages
    assert "reduce" in stages


@pytest.mark.asyncio
async def test_explicit_domain_overrides_rules() -> None:
    config = make_test_config()
    engine = build_engine(config, llm_client=make_stub_client(config))
    result = await engine.summarize(
        SummarizeRequest(content="Subject: hello", domain="news")
    )
    assert result.domain == "news"


def test_v2_endpoint_shape() -> None:
    config = make_test_config()
    service_engine = build_engine(config, llm_client=make_stub_client(config))
    client = TestClient(create_app(config=config, engine=service_engine))
    response = client.post(
        "/v2/summarize",
        json={"content": "Subject: demo\nAction item: reply"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["trace"]


def test_richmail_compat_unchanged() -> None:
    config = make_test_config()
    from agenticx_service.summarizer import SummarizerService

    service = SummarizerService(config, llm_client=make_stub_client(config))
    client = TestClient(create_app(config=config, service=service))
    response = client.post(
        "/aibox/richMail/v1.0/intelliAbstract?sid=demo",
        json={"email_content": "Subject: Sync\nPlease confirm Friday attendance."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["text"]
    assert body["data"]["scenario"] == "email"
    assert body["data"]["overflow_level"] >= 1


def test_core_has_no_business_words() -> None:
    core_dir = Path(__file__).resolve().parent.parent / "core"
    pattern = __import__("re").compile(r"\b(email|news|mail)\b", __import__("re").I)
    for path in core_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert not pattern.search(text), f"business word found in {path.name}"
