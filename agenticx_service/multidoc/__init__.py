"""Multi-document collection summarization.

Author: Damon Li
"""

from agenticx_service.multidoc.collection import CollectionSummarizer
from agenticx_service.multidoc.types import (
    CollectionIntent,
    CollectionRequest,
    CollectionResult,
    DocInput,
)

__all__ = [
    "CollectionIntent",
    "CollectionRequest",
    "CollectionResult",
    "CollectionSummarizer",
    "DocInput",
]
