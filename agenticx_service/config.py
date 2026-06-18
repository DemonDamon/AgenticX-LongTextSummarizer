"""Extended configuration for Summarizer v2.

Author: Damon Li
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

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
class DomainSettings:
    default: str = "email"


@dataclass
class ModalitySettings:
    liteparse_enabled: bool = True
    code_max_chars: int = 8000
    document_max_chars: int = 12000
    image_max_bytes: int = 5_000_000
    max_images: int = 5


@dataclass
class BatchSettings:
    batch_concurrency: int = 4
    queue_max: int = 100
    inline_max_concurrency: int = 2
    provider_rpm_limit: int = 60
    provider_tpm_limit: int = 120_000
    avg_call_seconds: float = 3.0
    output_budget_tokens: int = 512
    reduce_fan_in: int = 8


@dataclass
class MultidocSettings:
    sync_max_docs: int = 5
    sync_max_calls: int = 20
    per_doc_summary_max_tokens: int = 800


@dataclass
class AgenticSettings:
    layered_resolver: bool = False
    skill_authoring: bool = False
    personalization_max_chars: int = 400
    frozen_dir: str = "prompts/frozen"
    skills_dir: str = ""


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
    domains: DomainSettings = field(default_factory=DomainSettings)
    modality: ModalitySettings = field(default_factory=ModalitySettings)
    batch: BatchSettings = field(default_factory=BatchSettings)
    multidoc: MultidocSettings = field(default_factory=MultidocSettings)
    agentic: AgenticSettings = field(default_factory=AgenticSettings)
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

    agentic_raw = _section(raw, "agentic")
    if os.environ.get("AGX_SUMMARIZER_LAYERED_RESOLVER", "").lower() in {"1", "true", "yes"}:
        agentic_raw = {**agentic_raw, "layered_resolver": True}

    return AppConfig(
        server=ServiceSettings(**{**_section(raw, "server")}),
        llm=LLMSettings(**{**llm_raw, "api_key": api_key}),
        prompts=PromptSettings(**{**_section(raw, "prompts")}),
        domains=DomainSettings(**{**_section(raw, "domains")}),
        modality=ModalitySettings(**{**_section(raw, "modality")}),
        batch=BatchSettings(**{**_section(raw, "batch")}),
        multidoc=MultidocSettings(**{**_section(raw, "multidoc")}),
        agentic=AgenticSettings(**{**agentic_raw}),
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
