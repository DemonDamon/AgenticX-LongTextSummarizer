"""Service wiring helpers.

Author: Damon Li
"""

from __future__ import annotations

from pathlib import Path

from agenticx_service.agentic.personalization import PersonalizationStore
from agenticx_service.agentic.prompt_freeze import FrozenPromptStore
from agenticx_service.agentic.skill_author import SkillPromptProvider
from agenticx_service.config import AppConfig
from agenticx_service.core.engine import SummarizationEngine
from agenticx_service.core.prompt_resolver import LayeredPromptResolver, PromptResolver, StaticPromptResolver
from agenticx_service.domains import build_domain_registry
from agenticx_service.llm_client import LLMClient
from agenticx_service.prompts.registry import PromptRegistry

_SERVICE_ROOT = Path(__file__).resolve().parent


def build_prompt_resolver(
    config: AppConfig,
    registry,
    prompts: PromptRegistry,
) -> PromptResolver:
    static = StaticPromptResolver(registry, prompts)
    if not config.agentic.layered_resolver:
        return static
    frozen_dir = _SERVICE_ROOT / config.agentic.frozen_dir
    return LayeredPromptResolver(
        static,
        frozen_store=FrozenPromptStore(frozen_dir),
        skill_provider=SkillPromptProvider(config),
        personalization=PersonalizationStore(config),
    )


def build_engine(
    config: AppConfig,
    llm_client: LLMClient | None = None,
    prompt_registry: PromptRegistry | None = None,
) -> SummarizationEngine:
    prompts = prompt_registry or PromptRegistry()
    registry = build_domain_registry(config)
    resolver = build_prompt_resolver(config, registry, prompts)
    return SummarizationEngine(
        config,
        llm_client,
        prompts,
        domain_registry=registry,
        prompt_resolver=resolver,
    )
