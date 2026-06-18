"""News domain rule engine.

Author: Damon Li
"""

from __future__ import annotations

import re

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


class NewsRuleEngine:
    """Score content for news-domain affinity (0–1)."""

    def score(self, content: str) -> float:
        lowered = content.lower()
        hits = sum(1 for hint in _NEWS_HINTS if hint.lower() in lowered)
        if re.search(r"^【.+】", content, flags=re.MULTILINE):
            hits += 2
        if not hits:
            return 0.0
        return min(1.0, hits / 4.0)
