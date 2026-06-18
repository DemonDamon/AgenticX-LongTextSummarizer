"""Modality adapter protocol and capability matrix.

Author: Damon Li
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from agenticx.core.token_counter import truncate_text

from agenticx_service.config import AppConfig
from agenticx_service.core.types import ContentPart, Modality


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
    def assert_supported(part: ContentPart, supported: set[Modality]) -> None:
        if part.modality not in supported:
            raise ValueError(
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
        raise ValueError(f"No adapter for modality {part.modality}")

    async def assemble(
        self,
        parts: list[ContentPart],
        supported: set[Modality],
    ) -> tuple[str, list[str]]:
        blocks: list[str] = []
        trace: list[str] = []
        for part in parts:
            CapabilityMatrix.assert_supported(part, supported)
            adapter = self._adapter_for(part)
            repr_ = await adapter.to_text(part, {})
            trace.append(part.modality.value)
            label = repr_.note or part.modality.value
            blocks.append(f"[{label}]\n{repr_.text}")
        return "\n\n".join(blocks), trace


def clamp_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return truncate_text(text, max_chars=max_chars)
