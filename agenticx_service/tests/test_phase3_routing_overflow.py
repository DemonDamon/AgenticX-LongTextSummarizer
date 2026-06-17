"""Phase 3 routing and overflow tests.

Author: Damon Li
"""

from __future__ import annotations

import pytest

from agenticx_service.intent import IntentClassifier
from agenticx_service.overflow import OverflowGuard
from agenticx_service.summarizer import SummarizerService
from agenticx_service.tests.conftest import make_stub_client, make_test_config


@pytest.mark.asyncio
async def test_intent_email_vs_news() -> None:
    classifier = IntentClassifier(make_test_config().intent)
    email = "Subject: Project update\nPlease reply to confirm the rollout owner."
    news = "【报道】记者获悉，某市宣布扩建算力中心，项目总投资达120亿元。"
    assert await classifier.classify(email) == "email"
    assert await classifier.classify(news) == "news"


def test_overflow_emergency_truncation() -> None:
    config = make_test_config(overflow={"max_input_tokens": 50})
    guard = OverflowGuard(config.overflow, model="gpt-4o-mini")
    huge = "OVERFLOW_TEST sentence. " * 5000
    result = guard.guard_input(huge)
    assert result.level >= 3
    assert len(result.text) < len(huge)


@pytest.mark.asyncio
async def test_news_uses_news_scenario() -> None:
    config = make_test_config()
    service = SummarizerService(config, llm_client=make_stub_client(config))
    result = await service.summarize("【报道】记者获悉，某市宣布扩建算力中心。", scenario="news")
    assert result.scenario == "news"


@pytest.mark.asyncio
async def test_overflow_failure_returns_message_not_raise() -> None:
    config = make_test_config(overflow={"max_input_tokens": 50})
    provider = make_stub_client(config)

    class FailingProvider:
        async def ainvoke(self, prompt, **kwargs):  # noqa: ANN001
            raise RuntimeError("simulated provider failure")

    service = SummarizerService(config, llm_client=provider)
    service.llm.llm = FailingProvider()
    huge = "Fail me " * 2000
    result = await service.summarize(huge)
    assert "Unable to produce a complete summary" in result.text
    assert result.overflow_level == 4
