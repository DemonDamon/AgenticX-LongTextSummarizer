"""News domain plugin.

Author: Damon Li
"""

from __future__ import annotations

from agenticx_service.core.types import Modality
from agenticx_service.domains.news.rules import NewsRuleEngine


class NewsDomainPlugin:
    name = "news"
    rule_engine = NewsRuleEngine()

    def prompt_ids(self) -> dict[str, str]:
        return {
            "single": "news.single",
            "map": "news.map",
            "reduce": "news.reduce",
        }

    def supported_modalities(self) -> set[Modality]:
        return {Modality.TEXT, Modality.IMAGE}

    def postprocess(self, summary: str, ctx: dict) -> str:
        return summary
