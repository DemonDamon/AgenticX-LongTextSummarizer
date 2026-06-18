"""Image modality adapter (caption/OCR placeholder).

Author: Damon Li
"""

from __future__ import annotations

from typing import Any

from agenticx_service.config import AppConfig
from agenticx_service.core.types import ContentPart, Modality
from agenticx_service.modality.base import TextRepr


class ImageAdapter:
    modality = Modality.IMAGE

    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def can_handle(self, part: ContentPart) -> bool:
        return part.modality == Modality.IMAGE

    async def to_text(self, part: ContentPart, ctx: dict[str, Any]) -> TextRepr:
        caption = part.meta.get("caption") or part.meta.get("ocr_text")
        if caption:
            return TextRepr(text=str(caption), source_modality=Modality.IMAGE, note="image-caption")
        filename = part.meta.get("filename", "image")
        placeholder = (
            f"[Image: {filename}] Vision caption unavailable; "
            "provide caption or ocr_text in part.meta for richer summaries."
        )
        return TextRepr(text=placeholder, source_modality=Modality.IMAGE, note="image-placeholder")
