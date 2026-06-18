"""Text modality adapter (pass-through).

Author: Damon Li
"""

from __future__ import annotations

from typing import Any

from agenticx_service.core.types import ContentPart, Modality
from agenticx_service.modality.base import TextRepr


class TextAdapter:
    modality = Modality.TEXT

    def can_handle(self, part: ContentPart) -> bool:
        return part.modality == Modality.TEXT

    async def to_text(self, part: ContentPart, ctx: dict[str, Any]) -> TextRepr:
        return TextRepr(text=part.payload, source_modality=Modality.TEXT, note="text")
