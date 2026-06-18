"""Document modality adapter (liteparse when available).

Author: Damon Li
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agenticx_service.config import AppConfig
from agenticx_service.core.types import ContentPart, Modality
from agenticx_service.modality.base import TextRepr, clamp_text


class DocumentAdapter:
    modality = Modality.DOCUMENT

    def __init__(self, config: AppConfig) -> None:
        self.max_chars = config.modality.document_max_chars
        self.use_liteparse = config.modality.liteparse_enabled

    def can_handle(self, part: ContentPart) -> bool:
        return part.modality == Modality.DOCUMENT

    async def to_text(self, part: ContentPart, ctx: dict[str, Any]) -> TextRepr:
        if self.use_liteparse and part.payload and Path(part.payload).exists():
            try:
                from agenticx.tools.liteparse_adapter import LiteParseAdapter

                adapter = LiteParseAdapter()
                parsed = await adapter.parse(part.payload)
                text = parsed.get("text") or ""
                if not text and isinstance(parsed.get("pages"), list):
                    text = "\n".join(p.get("text", "") for p in parsed["pages"])
                if text:
                    return TextRepr(
                        text=clamp_text(text, self.max_chars),
                        source_modality=Modality.DOCUMENT,
                        note="document-liteparse",
                    )
            except Exception:  # noqa: BLE001
                pass
        filename = part.meta.get("filename", "document")
        inline = part.payload if not Path(part.payload).exists() else f"[file:{filename}]"
        return TextRepr(
            text=clamp_text(str(inline), self.max_chars),
            source_modality=Modality.DOCUMENT,
            note="document-inline",
        )
