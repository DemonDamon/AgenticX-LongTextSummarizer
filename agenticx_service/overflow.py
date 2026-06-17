"""Token overflow guardrails for summarization requests.

Author: Damon Li
"""

from __future__ import annotations

from dataclasses import dataclass

from agenticx.core.token_counter import count_tokens, truncate_text

from agenticx_service.config import OverflowSettings


@dataclass
class GuardResult:
    text: str
    level: int
    note: str = ""


class OverflowGuard:
    """Apply lightweight overflow protection without Agent OverflowRecoveryPipeline."""

    def __init__(self, settings: OverflowSettings, model: str) -> None:
        self.settings = settings
        self.model = model

    def guard_input(self, text: str) -> GuardResult:
        tokens = count_tokens(text, model=self.model)
        if tokens <= self.settings.max_input_tokens:
            return GuardResult(text=text, level=1)

        target = max(1000, self.settings.max_input_tokens // 2)
        truncated = truncate_text(text, max_tokens=target, model=self.model)
        return GuardResult(
            text=truncated,
            level=3,
            note="Input exceeded safe token budget and was truncated before summarization.",
        )

    def wrap_result(self, summary: str, guard: GuardResult) -> str:
        if guard.level <= 1 or not guard.note:
            return summary
        return f"{summary}\n\n[Note] {guard.note}"

    def failure_message(self) -> str:
        return (
            "Unable to produce a complete summary for this input. "
            "The content is too large or could not be processed safely."
        )
