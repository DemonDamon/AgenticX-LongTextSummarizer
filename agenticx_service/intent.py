"""Intent classification adapter over domain rule engines.

Author: Damon Li
"""

from __future__ import annotations

from typing import Literal

from agenticx_service.config import AppConfig, IntentSettings
from agenticx_service.domains import build_domain_registry
from agenticx_service.llm_client import LLMClient
from agenticx_service.prompts.registry import PromptRegistry

Scenario = Literal["email", "news"]


class IntentClassifier:
    """Route content to email or news summarization templates."""

    def __init__(
        self,
        settings: IntentSettings,
        llm_client: LLMClient | None = None,
        prompt_registry: PromptRegistry | None = None,
        *,
        config: AppConfig | None = None,
    ) -> None:
        self.settings = settings
        self.llm = llm_client
        self.prompts = prompt_registry or PromptRegistry()
        app_config = config or AppConfig(intent=settings)
        self.registry = build_domain_registry(app_config)

    async def classify(self, content: str) -> Scenario:
        rule_result = self._classify_by_rules(content)
        if self.settings.mode == "rule":
            return rule_result or "email"

        if self.settings.mode == "hybrid" and rule_result is not None:
            return rule_result

        if self.llm is None:
            return rule_result or "email"

        label = await self._classify_by_llm(content)
        return label if label in ("email", "news") else "email"

    def _classify_by_rules(self, content: str) -> Scenario | None:
        plugin = self.registry.resolve(content, explicit=None)
        email_score = self.registry.get("email").rule_engine.score(content)
        news_score = self.registry.get("news").rule_engine.score(content)
        if email_score > news_score and email_score > 0:
            return "email"
        if news_score > email_score and news_score > 0:
            return "news"
        if plugin.name in ("email", "news") and max(email_score, news_score) > 0:
            return plugin.name  # type: ignore[return-value]
        return None

    async def _classify_by_llm(self, content: str) -> str:
        snippet = content[:2000]
        prompt = self.prompts.format("intent_classifier", content=snippet)
        label = (await self.llm.complete(prompt)).strip().lower()
        if "news" in label:
            return "news"
        return "email"
