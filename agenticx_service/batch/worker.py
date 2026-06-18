"""Background worker consuming summarization jobs.

Author: Damon Li
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Callable, Awaitable

from agenticx_service.batch.queue import Job, JobQueue, JobStatus
from agenticx_service.config import AppConfig
from agenticx_service.core.engine import SummarizationEngine
from agenticx_service.core.types import SummarizeRequest
from agenticx_service.multidoc.collection import CollectionSummarizer
from agenticx_service.multidoc.types import CollectionRequest

logger = logging.getLogger(__name__)

JobHandler = Callable[[Job], Awaitable[dict[str, Any]]]


class SummaryWorker:
    """Async worker draining the job queue."""

    def __init__(
        self,
        config: AppConfig,
        queue: JobQueue,
        engine: SummarizationEngine,
        *,
        collection: CollectionSummarizer | None = None,
    ) -> None:
        self.config = config
        self.queue = queue
        self.engine = engine
        self.collection = collection or CollectionSummarizer(config, engine)
        self._semaphore = asyncio.Semaphore(config.batch.batch_concurrency)
        self._task: asyncio.Task[None] | None = None
        self._inflight_tasks: set[asyncio.Task[None]] = set()
        self.in_flight = 0

    async def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _run(self) -> None:
        while True:
            job = await self.queue.dequeue()
            task = asyncio.create_task(self._process(job))
            self._inflight_tasks.add(task)
            task.add_done_callback(self._inflight_tasks.discard)

    async def _process(self, job: Job) -> None:
        async with self._semaphore:
            self.in_flight += 1
            job.status = JobStatus.RUNNING
            self.queue.save(job)
            try:
                if job.job_type == "summarize":
                    result = await self._run_summarize(job.payload)
                elif job.job_type == "collection":
                    result = await self._run_collection(job.payload)
                elif job.job_type == "batch":
                    result = await self._run_batch(job.payload)
                else:
                    raise ValueError(f"Unknown job type: {job.job_type}")
                job.result = result
                job.status = JobStatus.DONE
            except Exception as exc:  # noqa: BLE001
                logger.exception("Job %s failed", job.job_id)
                job.error = str(exc)
                job.status = JobStatus.FAILED
            finally:
                job.finished_at = time.time()
                self.queue.save(job)
                self.in_flight -= 1

    async def _run_summarize(self, payload: dict[str, Any]) -> dict[str, Any]:
        req = SummarizeRequest(
            content=payload["content"],
            domain=payload.get("domain"),
            options=payload.get("options") or {},
            parts=payload.get("parts"),
        )
        result = await self.engine.summarize(req)
        return {
            "text": result.text,
            "domain": result.domain,
            "overflow_level": result.overflow_level,
            "trace": result.trace,
        }

    async def _run_collection(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = CollectionRequest.from_dict(payload)
        result = await self.collection.summarize(request)
        return result.to_dict()

    async def _run_batch(self, payload: dict[str, Any]) -> dict[str, Any]:
        items = payload.get("items", [])
        results = []
        for item in items:
            single = await self._run_summarize(item)
            results.append({"status": "done", "result": single})
        return {"items": results}
