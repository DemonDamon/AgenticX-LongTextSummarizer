"""Core data models for the summarization pipeline.

Author: Damon Li
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Modality(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    CODE = "code"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"


class Stage(str, Enum):
    SINGLE = "single"
    MAP = "map"
    REDUCE = "reduce"
    INTENT = "intent"


@dataclass
class ContentPart:
    modality: Modality
    payload: str
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class SummarizeRequest:
    content: str
    parts: list[ContentPart] | None = None
    domain: str | None = None
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class SummarizeResult:
    text: str
    domain: str
    overflow_level: int = 1
    trace: dict[str, Any] = field(default_factory=dict)

    @property
    def scenario(self) -> str:
        return self.domain
