"""Business-agnostic summarization core.

Author: Damon Li
"""

from agenticx_service.core.engine import SummarizationEngine
from agenticx_service.core.types import (
    Modality,
    Stage,
    SummarizeRequest,
    SummarizeResult,
)

__all__ = [
    "Modality",
    "Stage",
    "SummarizeRequest",
    "SummarizeResult",
    "SummarizationEngine",
]
