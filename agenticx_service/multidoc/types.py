"""Types for multi-document summarization.

Author: Damon Li
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from agenticx_service.core.types import ContentPart, Modality


class CollectionIntent(str, Enum):
    AGGREGATE = "aggregate"
    COMPARE = "compare"
    TIMELINE = "timeline"


@dataclass
class DocInput:
    doc_id: str
    content: str
    title: str | None = None
    domain: str | None = None
    parts: list[ContentPart] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DocInput:
        parts_raw = data.get("parts")
        parts = None
        if parts_raw:
            parts = [
                ContentPart(
                    modality=Modality(p["modality"]),
                    payload=p["payload"],
                    meta=p.get("meta") or {},
                )
                for p in parts_raw
            ]
        return cls(
            doc_id=data["doc_id"],
            content=data.get("content", ""),
            title=data.get("title"),
            domain=data.get("domain"),
            parts=parts,
        )


@dataclass
class CollectionRequest:
    docs: list[DocInput]
    intent: CollectionIntent = CollectionIntent.AGGREGATE
    options: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CollectionRequest:
        intent_raw = data.get("intent", "aggregate")
        intent = CollectionIntent(intent_raw)
        docs = [DocInput.from_dict(d) for d in data.get("docs", [])]
        return cls(docs=docs, intent=intent, options=data.get("options") or {})


@dataclass
class PerDocSummary:
    doc_id: str
    title: str | None
    summary: str


@dataclass
class CollectionResult:
    summary: str
    intent: CollectionIntent
    per_doc: list[PerDocSummary]
    trace: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "intent": self.intent.value,
            "per_doc": [
                {"doc_id": p.doc_id, "title": p.title, "summary": p.summary}
                for p in self.per_doc
            ],
            "trace": self.trace,
        }
