"""Email domain plugin.

Author: Damon Li
"""

from __future__ import annotations

from agenticx_service.core.types import Modality
from agenticx_service.domains.email.rules import EmailRuleEngine


class EmailDomainPlugin:
    name = "email"
    rule_engine = EmailRuleEngine()

    def prompt_ids(self) -> dict[str, str]:
        return {
            "single": "email.single",
            "map": "email.map",
            "reduce": "email.reduce",
        }

    def supported_modalities(self) -> set[Modality]:
        return {
            Modality.TEXT,
            Modality.CODE,
            Modality.IMAGE,
            Modality.DOCUMENT,
        }

    def postprocess(self, summary: str, ctx: dict) -> str:
        return summary
