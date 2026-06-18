"""Email domain rule engine.

Author: Damon Li
"""

from __future__ import annotations

import re

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


class EmailRuleEngine:
    """Score content for email-domain affinity (0–1)."""

    def score(self, content: str) -> float:
        lowered = content.lower()
        hits = sum(1 for hint in _EMAIL_HINTS if hint.lower() in lowered)
        if re.search(r"^subject:\s", lowered, flags=re.MULTILINE):
            hits += 2
        if not hits:
            return 0.0
        return min(1.0, hits / 4.0)
