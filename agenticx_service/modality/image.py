"""Image modality adapter (vision caption / OCR with graceful degradation).

Author: Damon Li
"""

from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Any

from agenticx.llms.vision import is_vision_capable

from agenticx_service.config import AppConfig
from agenticx_service.core.types import ContentPart, Modality
from agenticx_service.modality.base import TextRepr

logger = logging.getLogger(__name__)

_VISION_PROMPT = (
    "Describe this image briefly and extract any visible text (OCR). "
    "Reply in the same language as the visible text when possible."
)


class ImageAdapter:
    modality = Modality.IMAGE

    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def can_handle(self, part: ContentPart) -> bool:
        return part.modality == Modality.IMAGE

    def _image_url(self, part: ContentPart) -> str | None:
        payload = part.payload.strip()
        if not payload:
            return None
        mime = part.meta.get("mime", "image/png")
        if payload.startswith("data:"):
            return payload
        if payload.startswith("http://") or payload.startswith("https://"):
            return payload
        path = Path(payload)
        if path.exists():
            raw = path.read_bytes()
            if len(raw) > self.config.modality.image_max_bytes:
                logger.warning("Image file exceeds image_max_bytes; skipping vision call")
                return None
            encoded = base64.b64encode(raw).decode("ascii")
            return f"data:{mime};base64,{encoded}"
        if len(payload) > 40 and all(c.isalnum() or c in "+/=" for c in payload[:80]):
            return f"data:{mime};base64,{payload}"
        return None

    async def to_text(self, part: ContentPart, ctx: dict[str, Any]) -> TextRepr:
        caption = part.meta.get("caption") or part.meta.get("ocr_text")
        if caption:
            return TextRepr(text=str(caption), source_modality=Modality.IMAGE, note="image-caption")

        app_config = ctx.get("config")
        llm_client = ctx.get("llm_client")
        if app_config is not None and llm_client is not None:
            provider = app_config.llm.provider
            model = app_config.llm.model
            if is_vision_capable(provider, model):
                image_url = self._image_url(part)
                if image_url:
                    try:
                        messages = [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": _VISION_PROMPT},
                                    {"type": "image_url", "image_url": {"url": image_url}},
                                ],
                            }
                        ]
                        vision_text = await llm_client.complete(messages)
                        if vision_text.strip():
                            return TextRepr(
                                text=vision_text.strip(),
                                source_modality=Modality.IMAGE,
                                note="image-vision",
                            )
                    except Exception:  # noqa: BLE001
                        logger.warning(
                            "Vision caption failed for image; degrading to placeholder",
                            exc_info=True,
                        )

        filename = part.meta.get("filename", "image")
        placeholder = (
            f"[图片：{filename} 无法解析，已跳过]"
            if not is_vision_capable(
                getattr(app_config.llm, "provider", "") if app_config else "",
                getattr(app_config.llm, "model", "") if app_config else "",
            )
            else f"[Image: {filename}] Vision caption unavailable."
        )
        return TextRepr(
            text=placeholder,
            source_modality=Modality.IMAGE,
            note="vision-unavailable",
        )
