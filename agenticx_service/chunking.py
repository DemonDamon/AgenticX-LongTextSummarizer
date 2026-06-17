"""Chunking helpers for long-text summarization.

Author: Damon Li
"""

from __future__ import annotations

import logging
from typing import List, Optional

from agenticx.knowledge.base import ChunkingConfig
from agenticx.knowledge.chunkers import RecursiveChunker
from agenticx.knowledge.document import Document, DocumentMetadata

from agenticx_service.config import ChunkingSettings

logger = logging.getLogger(__name__)


class TextChunker:
    """Unified chunk splitter with recursive default and optional agentic mode."""

    def __init__(self, settings: ChunkingSettings) -> None:
        self.settings = settings
        self._config = ChunkingConfig(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        self._recursive = RecursiveChunker(self._config)

    async def split(self, text: str) -> List[str]:
        if self.settings.strategy == "agentic":
            agentic_chunks = await self._split_agentic(text)
            if agentic_chunks:
                return agentic_chunks
            logger.warning("Agentic chunker unavailable; falling back to recursive chunking")

        document = Document(
            content=text,
            metadata=DocumentMetadata(name="summarizer_input", source="inline", source_type="text"),
        )
        result = await self._recursive.chunk_document_async(document)
        return [chunk.content.strip() for chunk in result.chunks if chunk.content.strip()]

    async def _split_agentic(self, text: str) -> Optional[List[str]]:
        try:
            from agenticx.knowledge.chunkers import AgenticChunker
        except ImportError:
            return None

        try:
            chunker = AgenticChunker(self._config)
            document = Document(content=text)
            result = await chunker.chunk_document_async(document)
            contents = [chunk.content for chunk in result.chunks if chunk.content.strip()]
            return contents or None
        except TypeError:
            return None
        except Exception:  # noqa: BLE001
            logger.exception("Agentic chunking failed")
            return None
