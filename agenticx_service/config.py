"""Configuration loading for the AgenticX summarizer service.

Author: Damon Li
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

from agenticx.knowledge.graphers.config import LLMConfig


@dataclass
class LLMSettings:
    provider: str = "litellm"
    model: str = "gpt-4o-mini"
    api_key: str = ""
    base_url: str = ""
    temperature: float = 0.7

    def to_llm_config(self) -> LLMConfig:
        provider = self.provider or "litellm"
        return LLMConfig(
            type=provider,
            provider=provider,
            model=self.model or None,
            api_key=self.api_key or None,
            base_url=self.base_url or None,
            temperature=self.temperature,
        )


@dataclass
class ServiceSettings:
    host: str = "0.0.0.0"
    port: int = 8282


@dataclass
class PromptSettings:
    version: str = "v4"


@dataclass
class ChunkingSettings:
    strategy: str = "recursive"
    chunk_size: int = 4000
    chunk_overlap: int = 200
    max_single_pass_tokens: int = 3000
    map_concurrency: int = 4
    max_reduce_rounds: int = 3


@dataclass
class IntentSettings:
    mode: str = "rule"


@dataclass
class OverflowSettings:
    max_input_tokens: int = 120_000
    max_chunks: int = 50


@dataclass
class AppConfig:
    server: ServiceSettings = field(default_factory=ServiceSettings)
    llm: LLMSettings = field(default_factory=LLMSettings)
    prompts: PromptSettings = field(default_factory=PromptSettings)
    chunking: ChunkingSettings = field(default_factory=ChunkingSettings)
    intent: IntentSettings = field(default_factory=IntentSettings)
    overflow: OverflowSettings = field(default_factory=OverflowSettings)
    judge_llm: LLMSettings = field(default_factory=LLMSettings)

    def to_llm_config(self) -> LLMConfig:
        return self.llm.to_llm_config()

    def to_judge_llm_config(self) -> LLMConfig:
        return self.judge_llm.to_llm_config()


def _section(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key, {})
    return value if isinstance(value, dict) else {}


def load_config(path: str | Path) -> AppConfig:
    """Load YAML config and apply environment overrides."""
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    llm_raw = _section(raw, "llm")
    judge_raw = _section(raw, "judge_llm")
    api_key = os.environ.get("AGX_LLM_API_KEY", llm_raw.get("api_key", "") or "")
    judge_api_key = os.environ.get(
        "AGX_JUDGE_API_KEY",
        judge_raw.get("api_key", "") or api_key,
    )

    return AppConfig(
        server=ServiceSettings(**{**_section(raw, "server")}),
        llm=LLMSettings(**{**llm_raw, "api_key": api_key}),
        prompts=PromptSettings(**{**_section(raw, "prompts")}),
        chunking=ChunkingSettings(**{**_section(raw, "chunking")}),
        intent=IntentSettings(**{**_section(raw, "intent")}),
        overflow=OverflowSettings(**{**_section(raw, "overflow")}),
        judge_llm=LLMSettings(
            **{
                **llm_raw,
                **judge_raw,
                "api_key": judge_api_key,
            }
        ),
    )


def default_config_path() -> Path:
    """Resolve default config path relative to the example project root."""
    return Path(__file__).resolve().parent.parent / "config_agenticx.yaml"
