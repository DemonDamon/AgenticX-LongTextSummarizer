"""Audio/video modality skeleton (not supported in v2 baseline).

Future hook: wire ASR/transcription service (e.g. OpenAI Whisper, vendor ASR)
before handing plain text to SummarizationEngine.

Author: Damon Li
"""

from __future__ import annotations

from typing import Any

from agenticx_service.core.types import ContentPart, Modality
from agenticx_service.modality.base import ModalityNotSupported, TextRepr


class AudioVideoNotSupportedError(ModalityNotSupported):
    """Backward-compatible alias for audio/video rejection."""


class AudioVideoAdapter:
    modality = Modality.AUDIO

    def can_handle(self, part: ContentPart) -> bool:
        return part.modality in {Modality.AUDIO, Modality.VIDEO}

    async def to_text(self, part: ContentPart, ctx: dict[str, Any]) -> TextRepr:
        raise ModalityNotSupported(
            "audio/video summarization not enabled in this release"
        )
