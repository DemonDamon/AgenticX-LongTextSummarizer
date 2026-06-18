"""Code modality adapter.

Author: Damon Li
"""

from __future__ import annotations

from typing import Any

from agenticx_service.config import AppConfig
from agenticx_service.core.types import ContentPart, Modality
from agenticx_service.modality.base import TextRepr, clamp_text


class CodeAdapter:
    modality = Modality.CODE

    def __init__(self, config: AppConfig) -> None:
        self.max_chars = config.modality.code_max_chars

    def can_handle(self, part: ContentPart) -> bool:
        return part.modality == Modality.CODE

    async def to_text(self, part: ContentPart, ctx: dict[str, Any]) -> TextRepr:
        language = part.meta.get("language", "")
        body = clamp_text(part.payload, self.max_chars)
        fenced = f"```{language}\n{body}\n```" if language else f"```\n{body}\n```"
        return TextRepr(text=fenced, source_modality=Modality.CODE, note="code")
