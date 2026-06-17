"""Phase 4 evaluation tests.

Author: Damon Li
"""

from __future__ import annotations

import pytest

from agenticx_service.evaluation.judges import build_composite_judge, evaluate_dimensions
from agenticx_service.evaluation.run_eval import (
    _expand_input,
    _hard_assertions,
    _overflow_hard_assertions,
    _load_cases,
    run_evaluation,
)
from agenticx_service.summarizer import SummarizeResult
from agenticx_service.tests.conftest import make_test_config


def test_pii_hard_assertion() -> None:
    failures = _hard_assertions(
        "Please call alice@example.com",
        {"must_not": ["alice@example.com"]},
    )
    assert failures


def test_overflow_hard_assertion_empty_summary() -> None:
    failures = _overflow_hard_assertions(
        {"require_no_crash": True},
        SummarizeResult(text="", overflow_level=3, scenario="news"),
    )
    assert failures


def test_dataset_has_four_unique_cases() -> None:
    cases = _load_cases()
    ids = [case["id"] for case in cases]
    assert len(ids) == 4
    assert len(set(ids)) == 4


def test_expand_input_supports_tail() -> None:
    text = _expand_input(
        {
            "input": "BODY",
            "repeat": 2,
            "tail": "TAIL",
        }
    )
    assert text == "BODYBODYTAIL"


@pytest.mark.asyncio
async def test_run_eval_generates_report() -> None:
    config = make_test_config()
    report = await run_evaluation(config=config, use_mock_judge=True)
    assert report["total"] == 4
    assert report["passed"] >= 0
    assert "items" in report
    first = report["items"][0]
    assert "dimension_scores" in first
    assert "faithfulness" in first["dimension_scores"]
    assert "conciseness" in first["dimension_scores"]


@pytest.mark.asyncio
async def test_composite_judge_mock_mode() -> None:
    judge = build_composite_judge(use_mock=True, scenario="email")
    result = await judge.evaluate(output="A concise faithful summary.")
    assert result.reason


@pytest.mark.asyncio
async def test_dimension_judges_email_and_news() -> None:
    email_scores = await evaluate_dimensions(
        output="Please confirm attendance by Friday.",
        scenario="email",
        use_mock=True,
    )
    assert set(email_scores) == {
        "faithfulness",
        "conciseness",
        "action_item_coverage",
    }

    news_scores = await evaluate_dimensions(
        output="2026年6月，某市宣布扩建算力中心。",
        scenario="news",
        use_mock=True,
    )
    assert set(news_scores) == {
        "faithfulness",
        "conciseness",
        "fact_5w1h_coverage",
    }
