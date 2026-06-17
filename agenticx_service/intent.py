"""Intent classification for email vs news routing.

Author: Damon Li
"""

from __future__ import annotations

import re
from typing import Literal

from agenticx_service.config import IntentSettings
from agenticx_service.llm_client import LLMClient
from agenticx_service.prompts.registry import PromptRegistry

Scenario = Literal["email", "news"]

_EMAIL_HINTS = (
    "发件人",
    "收件人",
    "回复",
    "转发",
    "re:",
    "fw:",
    "subject:",
    "dear ",
    "best regards",
    "action item",
)

_NEWS_HINTS = (
    "记者",
    "报道",
    "据悉",
    "本报讯",
    "新华社",
    "Reuters",
    "breaking",
    "according to",
)


class IntentClassifier:
    """Route content to email or news summarization templates."""

    def __init__(
        self,
        settings: IntentSettings,
        llm_client: LLMClient | None = None,
        prompt_registry: PromptRegistry | None = None,
    ) -> None:
        self.settings = settings
        self.llm = llm_client
        self.prompts = prompt_registry or PromptRegistry()

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
        lowered = content.lower()
        email_score = sum(1 for hint in _EMAIL_HINTS if hint.lower() in lowered)
        news_score = sum(1 for hint in _NEWS_HINTS if hint.lower() in lowered)

        if re.search(r"^subject:\s", lowered, flags=re.MULTILINE):
            email_score += 2
        if re.search(r"^【.+】", content, flags=re.MULTILINE):
            news_score += 2

        if email_score > news_score:
            return "email"
        if news_score > email_score:
            return "news"
        return None

    async def _classify_by_llm(self, content: str) -> str:
        snippet = content[:2000]
        prompt = self.prompts.format("intent_classifier", content=snippet)
        label = (await self.llm.complete(prompt)).strip().lower()
        if "news" in label:
            return "news"
        return "email"
