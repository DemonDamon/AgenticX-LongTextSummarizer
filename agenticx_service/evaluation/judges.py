"""LLMJudge-based evaluators for summarization quality.

Author: Damon Li
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Protocol

from agenticx.evaluation.llm_judge import CompositeJudge, JudgeMode, JudgeResult, LLMJudge, MockLLMProvider

from agenticx_service.llm_client import LLMClient

FAITHFULNESS_RUBRIC = (
    "The summary must stay faithful to the source and must not invent facts."
)
CONCISENESS_RUBRIC = (
    "The summary should be concise and suitable for quick reading."
)
ACTION_ITEM_RUBRIC = (
    "The summary should capture action items that require recipient reply or confirmation."
)
FACT_5W1H_RUBRIC = (
    "The summary should cover core 5W1H facts and the article's main viewpoint."
)


class JudgeProvider(Protocol):
    async def acomplete(self, prompt: str) -> str: ...

    def complete(self, prompt: str) -> str: ...


class JudgeLLMAdapter:
    """Adapt LLMClient to the evaluation provider protocol."""

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    async def acomplete(self, prompt: str) -> str:
        return await self.llm_client.complete(prompt)

    def complete(self, prompt: str) -> str:
        import asyncio

        return asyncio.run(self.acomplete(prompt))


@dataclass(frozen=True)
class DimensionJudge:
    name: str
    judge: LLMJudge


def build_dimension_judges(
    scenario: str = "email",
    llm_client: LLMClient | None = None,
    use_mock: bool = False,
) -> List[DimensionJudge]:
    """Build named dimension judges for a scenario."""
    provider: JudgeProvider = MockLLMProvider() if use_mock else JudgeLLMAdapter(llm_client)  # type: ignore[assignment]

    dimensions = [
        DimensionJudge("faithfulness", LLMJudge(FAITHFULNESS_RUBRIC, JudgeMode.BINARY, provider)),
        DimensionJudge("conciseness", LLMJudge(CONCISENESS_RUBRIC, JudgeMode.BINARY, provider)),
    ]
    if scenario == "news":
        dimensions.append(
            DimensionJudge(
                "fact_5w1h_coverage",
                LLMJudge(FACT_5W1H_RUBRIC, JudgeMode.BINARY, provider),
            )
        )
    else:
        dimensions.append(
            DimensionJudge(
                "action_item_coverage",
                LLMJudge(ACTION_ITEM_RUBRIC, JudgeMode.BINARY, provider),
            )
        )
    return dimensions


def build_composite_judge(
    llm_client: LLMClient | None = None,
    scenario: str = "email",
    use_mock: bool = False,
) -> CompositeJudge:
    """Create scenario-aware composite judges."""
    dimensions = build_dimension_judges(scenario, llm_client, use_mock=use_mock)
    return CompositeJudge(judges=[item.judge for item in dimensions], aggregation="all")


async def evaluate_dimensions(
    output: str,
    scenario: str,
    llm_client: LLMClient | None = None,
    use_mock: bool = False,
    inputs: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Evaluate each dimension separately for per-dimension reporting."""
    scores: dict[str, dict[str, Any]] = {}
    for dimension in build_dimension_judges(scenario, llm_client, use_mock=use_mock):
        result: JudgeResult = await dimension.judge.evaluate(output=output, inputs=inputs)
        scores[dimension.name] = {
            "passed": bool(result.value),
            "reason": result.reason,
        }
    return scores
