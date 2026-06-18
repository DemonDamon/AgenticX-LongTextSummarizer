"""Resource estimation and capacity guard for batch summarization.

Author: Damon Li
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from agenticx_service.config import AppConfig, BatchSettings, ChunkingSettings


@dataclass(frozen=True)
class ResourceEstimate:
    n_chunks: int
    calls: int
    est_latency_s: float
    required_tpm: float
    required_rpm: float
    est_mem_bytes: int


class ResourceEstimator:
    """Compute LLM call counts and provider load from token sizes."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def estimate_single(self, token_count: int, cfg: AppConfig | None = None) -> ResourceEstimate:
        app = cfg or self.config
        chunking = app.chunking
        batch = app.batch
        threshold = chunking.max_single_pass_tokens
        chunk_size = chunking.chunk_size

        if token_count <= threshold:
            calls = 1
            n_chunks = 1
        else:
            n_chunks = max(1, math.ceil(token_count / chunk_size))
            map_calls = n_chunks
            reduce_calls = self._reduce_calls(n_chunks, batch.reduce_fan_in, chunking.max_reduce_rounds)
            calls = map_calls + reduce_calls

        est_latency = math.ceil(calls / max(1, chunking.map_concurrency)) * batch.avg_call_seconds
        tokens_per_call = min(token_count, chunk_size) + batch.output_budget_tokens
        required_tpm = (calls * tokens_per_call) / max(est_latency / 60.0, 1 / 60.0)
        required_rpm = calls / max(est_latency / 60.0, 1 / 60.0)
        est_mem = n_chunks * chunk_size * 4 * batch.batch_concurrency

        return ResourceEstimate(
            n_chunks=n_chunks,
            calls=calls,
            est_latency_s=est_latency,
            required_tpm=required_tpm,
            required_rpm=required_rpm,
            est_mem_bytes=est_mem,
        )

    def estimate_batch(self, token_counts: list[int], cfg: AppConfig | None = None) -> ResourceEstimate:
        app = cfg or self.config
        singles = [self.estimate_single(t, app) for t in token_counts]
        total_calls = sum(s.calls for s in singles)
        total_chunks = sum(s.n_chunks for s in singles)
        batch = app.batch
        est_latency = (
            math.ceil(total_calls / max(1, batch.batch_concurrency)) * batch.avg_call_seconds
        )
        tokens_per_call = app.batch.output_budget_tokens + app.chunking.chunk_size
        required_tpm = (total_calls * tokens_per_call) / max(est_latency / 60.0, 1 / 60.0)
        required_rpm = total_calls / max(est_latency / 60.0, 1 / 60.0)
        est_mem = sum(s.est_mem_bytes for s in singles)
        return ResourceEstimate(
            n_chunks=total_chunks,
            calls=total_calls,
            est_latency_s=est_latency,
            required_tpm=required_tpm,
            required_rpm=required_rpm,
            est_mem_bytes=est_mem,
        )

    @staticmethod
    def _reduce_calls(n_chunks: int, fan_in: int, max_rounds: int) -> int:
        remaining = n_chunks
        rounds = 0
        total = 0
        while remaining > 1 and rounds < max_rounds:
            groups = math.ceil(remaining / fan_in)
            total += groups
            remaining = groups
            rounds += 1
        return max(1, total)


Decision = Literal["inline", "enqueue", "reject"]


class CapacityGuard:
    """Decide whether a request can run inline, must enqueue, or be rejected."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def decide(
        self,
        estimate: ResourceEstimate,
        in_flight: int,
        queue_size: int,
    ) -> Decision:
        batch = self.config.batch
        if in_flight >= batch.inline_max_concurrency:
            if queue_size >= batch.queue_max:
                return "reject"
            return "enqueue"
        if estimate.required_rpm > batch.provider_rpm_limit:
            if queue_size >= batch.queue_max:
                return "reject"
            return "enqueue"
        if estimate.required_tpm > batch.provider_tpm_limit:
            if queue_size >= batch.queue_max:
                return "reject"
            return "enqueue"
        return "inline"
