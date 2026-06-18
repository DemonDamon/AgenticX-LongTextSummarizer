"""CLI entry for prompt evaluation and freeze.

Author: Damon Li
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from agenticx_service.agentic.eval_harness import PromptEvalHarness
from agenticx_service.agentic.prompt_freeze import FrozenPromptStore
from agenticx_service.config import default_config_path, load_config


async def _main_async(args: argparse.Namespace) -> None:
    harness = PromptEvalHarness()
    candidates = {
        "email.single": Path(args.candidate).read_text(encoding="utf-8")
        if args.candidate
        else "Summarize: {user_raw_text_input}",
    }
    scores = await harness.run(candidates, scenario=args.domain, dataset_name=args.dataset)
    winner = scores[0].candidate_id if scores else None
    print(f"Winner: {winner}")
    if args.freeze and winner:
        config = load_config(default_config_path())
        service_root = Path(__file__).resolve().parent.parent
        store = FrozenPromptStore(service_root / config.agentic.frozen_dir)
        template = candidates[winner]
        ver = store.freeze(args.domain, "single", template, meta={"candidate": winner})
        print(f"Frozen {args.domain}.single@{ver}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run prompt eval harness")
    parser.add_argument("--domain", default="email")
    parser.add_argument("--dataset", default="email_short.json")
    parser.add_argument("--candidate", default="")
    parser.add_argument("--freeze", action="store_true")
    args = parser.parse_args()
    asyncio.run(_main_async(args))


if __name__ == "__main__":
    main()
