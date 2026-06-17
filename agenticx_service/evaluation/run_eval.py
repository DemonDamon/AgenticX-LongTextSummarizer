"""Evaluation runner for summarizer datasets.

Author: Damon Li
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from agenticx_service.config import AppConfig, default_config_path, load_config
from agenticx_service.evaluation.judges import build_composite_judge, evaluate_dimensions
from agenticx_service.llm_client import LLMClient
from agenticx_service.summarizer import SummarizerService, SummarizeResult
from agenticx_service.stub_llm import make_stub_client

_DATASET_DIR = Path(__file__).resolve().parent / "datasets"


def _load_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for path in sorted(_DATASET_DIR.glob("*.json")):
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, list):
            cases.extend(payload)
    return cases


def _expand_input(case: dict[str, Any]) -> str:
    text = str(case.get("input", ""))
    repeat = int(case.get("repeat", 1))
    body = text * max(1, repeat)
    tail = case.get("tail")
    if tail:
        return body + str(tail)
    return body


def _hard_assertions(summary: str, case: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for forbidden in case.get("must_not", []):
        if forbidden and forbidden in summary:
            failures.append(f"Forbidden token present: {forbidden}")
    return failures


def _overflow_hard_assertions(case: dict[str, Any], result: SummarizeResult) -> list[str]:
    """Overflow cases must complete without crashing; degraded output is acceptable."""
    if not case.get("require_no_crash"):
        return []
    if not result.text.strip():
        return ["Overflow case returned empty summary"]
    return []


async def run_evaluation(
    config: AppConfig | None = None,
    use_mock_judge: bool = True,
) -> dict[str, Any]:
    """Run all evaluation datasets and return a structured report."""
    app_config = config or load_config(default_config_path())
    llm_client = make_stub_client(app_config) if use_mock_judge else None
    service = SummarizerService(app_config, llm_client=llm_client)
    judge_llm = None if use_mock_judge else LLMClient(
        AppConfig(
            server=app_config.server,
            llm=app_config.judge_llm,
            prompts=app_config.prompts,
            chunking=app_config.chunking,
            intent=app_config.intent,
            overflow=app_config.overflow,
            judge_llm=app_config.judge_llm,
        )
    )

    report_items: list[dict[str, Any]] = []
    for case in _load_cases():
        case_id = case["id"]
        scenario = case.get("scenario", "email")
        source_text = _expand_input(case)

        try:
            result = await service.summarize(source_text, scenario=scenario)
            hard_failures = _hard_assertions(result.text, case)
            hard_failures.extend(_overflow_hard_assertions(case, result))
            dimension_scores = await evaluate_dimensions(
                output=result.text,
                scenario=scenario,
                llm_client=judge_llm,
                use_mock=use_mock_judge,
                inputs={
                    "source": source_text,
                    "scenario": scenario,
                    "expected_points": case.get("expected_points", []),
                },
            )
            judge = build_composite_judge(
                llm_client=judge_llm,
                scenario=scenario,
                use_mock=use_mock_judge,
            )
            judge_result = await judge.evaluate(
                output=result.text,
                inputs={
                    "source": source_text,
                    "scenario": scenario,
                    "expected_points": case.get("expected_points", []),
                },
            )
            dimensions_passed = all(item["passed"] for item in dimension_scores.values())
            passed = not hard_failures and dimensions_passed and bool(judge_result.value)
            report_items.append(
                {
                    "id": case_id,
                    "scenario": scenario,
                    "passed": passed,
                    "summary": result.text,
                    "overflow_level": result.overflow_level,
                    "dimension_scores": dimension_scores,
                    "judge_reason": judge_result.reason,
                    "hard_failures": hard_failures,
                }
            )
        except Exception as exc:  # noqa: BLE001
            report_items.append(
                {
                    "id": case_id,
                    "scenario": scenario,
                    "passed": False,
                    "error": str(exc),
                    "hard_failures": ["Service crashed during overflow handling"],
                }
            )

    passed_count = sum(1 for item in report_items if item.get("passed"))
    report = {
        "timestamp": int(time.time()),
        "total": len(report_items),
        "passed": passed_count,
        "failed": len(report_items) - passed_count,
        "items": report_items,
    }

    output_dir = Path(__file__).resolve().parent
    json_path = output_dir / f"report_{report['timestamp']}.json"
    md_path = output_dir / f"report_{report['timestamp']}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Summarizer Evaluation Report",
        "",
        f"- Total: {report['total']}",
        f"- Passed: {report['passed']}",
        f"- Failed: {report['failed']}",
        "",
    ]
    for item in report_items:
        status = "PASS" if item.get("passed") else "FAIL"
        lines.append(f"## {item['id']} ({status})")
        if item.get("summary"):
            lines.append(item["summary"])
        dimension_scores = item.get("dimension_scores") or {}
        if dimension_scores:
            lines.append("")
            lines.append("### Dimension scores")
            for name, score in dimension_scores.items():
                dim_status = "pass" if score.get("passed") else "fail"
                lines.append(f"- {name}: {dim_status} — {score.get('reason', '')}")
        if item.get("overflow_level") is not None:
            lines.append(f"Overflow level: {item['overflow_level']}")
        if item.get("hard_failures"):
            lines.append(f"Hard failures: {item['hard_failures']}")
        if item.get("error"):
            lines.append(f"Error: {item['error']}")
        lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    report["json_path"] = str(json_path)
    report["markdown_path"] = str(md_path)
    return report


def main() -> None:
    import asyncio
    import os

    use_mock = os.getenv("AGX_EVAL_USE_MOCK_JUDGE", "1").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    result = asyncio.run(run_evaluation(use_mock_judge=use_mock))
    print(json.dumps({"passed": result["passed"], "failed": result["failed"]}, indent=2))


if __name__ == "__main__":
    main()
