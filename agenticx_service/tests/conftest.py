"""Shared test helpers.

Author: Damon Li
"""

from __future__ import annotations

from typing import Any

from agenticx_service.config import (
    AgenticSettings,
    AppConfig,
    BatchSettings,
    ChunkingSettings,
    DomainSettings,
    IntentSettings,
    LLMSettings,
    ModalitySettings,
    MultidocSettings,
    OverflowSettings,
    PromptSettings,
    ServiceSettings,
)
from agenticx_service.llm_client import LLMClient
from agenticx_service.stub_llm import StubLLMProvider, make_stub_client as _make_stub_client

__all__ = ["StubLLMProvider", "make_stub_client", "make_test_config"]


def make_test_config(**overrides: Any) -> AppConfig:
    chunking = ChunkingSettings(**overrides.pop("chunking", {}))
    overflow = OverflowSettings(**overrides.pop("overflow", {}))
    intent = IntentSettings(**overrides.pop("intent", {}))
    domains = DomainSettings(**overrides.pop("domains", {}))
    modality = ModalitySettings(**overrides.pop("modality", {}))
    batch = BatchSettings(**overrides.pop("batch", {}))
    multidoc = MultidocSettings(**overrides.pop("multidoc", {}))
    agentic = AgenticSettings(**overrides.pop("agentic", {}))
    return AppConfig(
        server=ServiceSettings(host="127.0.0.1", port=0),
        llm=LLMSettings(model="gpt-4o-mini"),
        prompts=PromptSettings(version="v4"),
        chunking=chunking,
        intent=intent,
        overflow=overflow,
        domains=domains,
        modality=modality,
        batch=batch,
        multidoc=multidoc,
        agentic=agentic,
        judge_llm=LLMSettings(model="gpt-4o-mini"),
        **overrides,
    )


def make_stub_client(config: AppConfig, content: str = "Stub summary output.") -> LLMClient:
    return _make_stub_client(config, content=content)
