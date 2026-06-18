"""Document modality adapter (liteparse when available).

Author: Damon Li
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from agenticx_service.config import AppConfig
from agenticx_service.core.types import ContentPart, Modality
from agenticx_service.modality.base import TextRepr, clamp_text

logger = logging.getLogger(__name__)

_LITEPARSE_INSTALL_HINT = "npm i -g @llamaindex/liteparse"


class DocumentAdapter:
    modality = Modality.DOCUMENT

    def __init__(self, config: AppConfig) -> None:
        self.max_chars = config.modality.document_max_chars
        self.use_liteparse = config.modality.liteparse_enabled

    def can_handle(self, part: ContentPart) -> bool:
        return part.modality == Modality.DOCUMENT

    async def to_text(self, part: ContentPart, ctx: dict[str, Any]) -> TextRepr:
        filename = part.meta.get("filename", "document")
        path = Path(part.payload) if part.payload else None

        if self.use_liteparse and path and path.exists():
            try:
                from agenticx.tools.adapters.liteparse import LiteParseAdapter

                adapter = LiteParseAdapter()
                if not adapter.is_available():
                    msg = (
                        f"[Document: {filename}] liteparse not installed. "
                        f"Install: {_LITEPARSE_INSTALL_HINT}"
                    )
                    return TextRepr(
                        text=msg,
                        source_modality=Modality.DOCUMENT,
                        note="document-liteparse-missing",
                    )
                text = await adapter.parse_to_text(path)
                if text.strip():
                    return TextRepr(
                        text=clamp_text(text, self.max_chars),
                        source_modality=Modality.DOCUMENT,
                        note="document-liteparse",
                    )
            except Exception:  # noqa: BLE001
                logger.warning("liteparse failed for %s", path, exc_info=True)

        inline = part.payload if not (path and path.exists()) else f"[file:{filename}]"
        return TextRepr(
            text=clamp_text(str(inline), self.max_chars),
            source_modality=Modality.DOCUMENT,
            note="document-inline",
        )
