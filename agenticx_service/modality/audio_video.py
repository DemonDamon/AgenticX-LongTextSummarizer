"""Audio/video modality skeleton (not supported in v2 baseline).

Author: Damon Li
"""

from __future__ import annotations

from typing import Any

from agenticx_service.core.types import ContentPart, Modality
from agenticx_service.modality.base import TextRepr


class AudioVideoNotSupportedError(ValueError):
    pass


class AudioVideoAdapter:
    modality = Modality.AUDIO

    def can_handle(self, part: ContentPart) -> bool:
        return part.modality in {Modality.AUDIO, Modality.VIDEO}

    async def to_text(self, part: ContentPart, ctx: dict[str, Any]) -> TextRepr:
        raise AudioVideoNotSupportedError(
            f"Modality {part.modality.value} is reserved but not supported yet"
        )
