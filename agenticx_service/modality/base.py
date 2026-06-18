"""Modality adapter protocol and capability matrix.

Author: Damon Li
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from agenticx_service.config import AppConfig
from agenticx_service.core.types import ContentPart, Modality

logger = logging.getLogger(__name__)


class ModalityNotSupported(ValueError):
    """Raised when a modality has no adapter or is explicitly disabled."""


@dataclass
class TextRepr:
    text: str
    source_modality: Modality
    note: str = ""


@runtime_checkable
class ModalityAdapter(Protocol):
    modality: Modality

    def can_handle(self, part: ContentPart) -> bool:
        ...

    async def to_text(self, part: ContentPart, ctx: dict[str, Any]) -> TextRepr:
        ...


class CapabilityMatrix:
    """Declare which modalities a domain supports."""

    @staticmethod
    def is_supported(part: ContentPart, supported: set[Modality]) -> bool:
        return part.modality in supported

    @staticmethod
    def assert_supported(part: ContentPart, supported: set[Modality]) -> None:
        if not CapabilityMatrix.is_supported(part, supported):
            raise ModalityNotSupported(
                f"Modality {part.modality.value} not supported for this domain"
            )


class ModalityPipeline:
    """Convert non-text parts to text before the core engine runs."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        from agenticx_service.modality.audio_video import AudioVideoAdapter
        from agenticx_service.modality.code import CodeAdapter
        from agenticx_service.modality.document import DocumentAdapter
        from agenticx_service.modality.image import ImageAdapter
        from agenticx_service.modality.text import TextAdapter

        self._adapters: list[ModalityAdapter] = [
            TextAdapter(),
            CodeAdapter(config),
            ImageAdapter(config),
            DocumentAdapter(config),
            AudioVideoAdapter(),
        ]

    def _adapter_for(self, part: ContentPart) -> ModalityAdapter:
        for adapter in self._adapters:
            if adapter.can_handle(part):
                return adapter
        raise ModalityNotSupported(f"No adapter for modality {part.modality.value}")

    async def assemble(
        self,
        parts: list[ContentPart],
        supported: set[Modality],
        ctx: dict[str, Any] | None = None,
    ) -> tuple[str, list[str]]:
        ctx = ctx or {}
        blocks: list[str] = []
        trace: list[str] = []
        image_count = 0
        max_images = self.config.modality.max_images

        for part in parts:
            if not CapabilityMatrix.is_supported(part, supported):
                trace.append(f"skipped:{part.modality.value}")
                logger.info(
                    "Skipping unsupported modality %s for domain capability set",
                    part.modality.value,
                )
                continue

            if part.modality == Modality.IMAGE:
                if image_count >= max_images:
                    trace.append("skipped:image-limit")
                    logger.warning(
                        "Dropped image part (max_images=%s exceeded)", max_images
                    )
                    continue
                image_count += 1

            adapter = self._adapter_for(part)
            repr_ = await adapter.to_text(part, ctx)
            trace.append(part.modality.value)
            if repr_.note in {"vision-unavailable", "image-placeholder"}:
                trace.append("degraded:image")
            label = repr_.note or part.modality.value
            blocks.append(f"[{label}]\n{repr_.text}")

        return "\n\n".join(blocks), trace


def clamp_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - 1)] + "…"
