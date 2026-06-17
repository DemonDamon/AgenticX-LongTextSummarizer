"""Phase 1 smoke tests.

Author: Damon Li
"""

from __future__ import annotations

import pytest

from agenticx_service.summarizer import SummarizerService
from agenticx_service.tests.conftest import make_stub_client, make_test_config
from agenticx_service.tools.desensitize import mask_pii


def test_desensitize_masks_pii() -> None:
    raw = "Contact alice@example.com or 13800138000 for details."
    masked = mask_pii(raw)
    assert "alice@example.com" not in masked
    assert "13800138000" not in masked
    assert "***" in masked


@pytest.mark.asyncio
async def test_summarize_short_email() -> None:
    config = make_test_config()
    service = SummarizerService(config, llm_client=make_stub_client(config))
    result = await service.summarize("Subject: Sync\nPlease confirm Friday attendance.")
    assert result.text
    assert result.scenario == "email"
