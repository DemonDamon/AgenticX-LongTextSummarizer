"""Cold-start batch evaluation for prompt candidates.

Author: Damon Li
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agenticx.evaluation.llm_judge import MockLLMProvider

from agenticx_service.evaluation.judges import evaluate_dimensions
from agenticx_service.tools.desensitize import mask_pii


@dataclass
class CandidateScore:
    candidate_id: str
    dimension_scores: dict[str, float] = field(default_factory=dict)
    hard_failures: int = 0
    composite: float = 0.0


class PromptEvalHarness:
    """Evaluate prompt candidates against datasets."""

    def __init__(self, output_dir: Path | None = None) -> None:
        service_root = Path(__file__).resolve().parent.parent
        self.output_dir = output_dir or service_root / "agentic"
        self.datasets_dir = service_root / "evaluation" / "datasets"

    async def run(
        self,
        candidates: dict[str, str],
        *,
        scenario: str = "email",
        dataset_name: str = "email_short.json",
    ) -> list[CandidateScore]:
        use_mock = os.environ.get("AGX_EVAL_USE_MOCK_JUDGE", "1").lower() not in {"0", "false", "no"}
        if use_mock:
            MockLLMProvider()

        dataset_path = self.datasets_dir / dataset_name
        items: list[dict[str, Any]] = []
        if dataset_path.exists():
            items = json.loads(dataset_path.read_text(encoding="utf-8"))

        scores: list[CandidateScore] = []
        for cid, template in candidates.items():
            dim_totals: dict[str, list[float]] = {}
            hard_failures = 0
            for item in items:
                content = item.get("content") or item.get("email_content") or ""
                prompt = template.format(user_raw_text_input=mask_pii(content))
                output = f"Stub summary for {scenario}"
                if "PII" in prompt or "password" in content.lower():
                    output = content
                dims = await evaluate_dimensions(
                    output,
                    scenario,
                    use_mock=use_mock,
                    inputs={"content": content},
                )
                for name, result in dims.items():
                    dim_totals.setdefault(name, []).append(1.0 if result["passed"] else 0.0)
                if "@" in content and "@" in output:
                    hard_failures += 1
            dimension_scores = {
                name: sum(vals) / max(len(vals), 1) for name, vals in dim_totals.items()
            }
            composite_score = sum(dimension_scores.values()) / max(len(dimension_scores), 1)
            composite_score -= hard_failures * 0.5
            scores.append(
                CandidateScore(
                    candidate_id=cid,
                    dimension_scores=dimension_scores,
                    hard_failures=hard_failures,
                    composite=composite_score,
                )
            )
        scores.sort(key=lambda s: s.composite, reverse=True)
        self._write_report(scores, candidates)
        return scores

    def _write_report(self, scores: list[CandidateScore], candidates: dict[str, str]) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"eval_report_{ts}.json"
        payload = {
            "ranking": [
                {
                    "candidate_id": s.candidate_id,
                    "composite": s.composite,
                    "hard_failures": s.hard_failures,
                    "dimension_scores": s.dimension_scores,
                }
                for s in scores
            ],
            "candidates": list(candidates.keys()),
        }
        report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        md_path = self.output_dir / f"eval_report_{ts}.md"
        lines = ["# Prompt Eval Report", ""]
        for rank, s in enumerate(scores, start=1):
            lines.append(f"{rank}. **{s.candidate_id}** — score={s.composite:.2f}, hard_fail={s.hard_failures}")
        md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return report_path
