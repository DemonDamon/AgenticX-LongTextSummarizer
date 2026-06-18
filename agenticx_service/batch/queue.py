"""In-memory job queue for async summarization.

Author: Damon Li
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class Job:
    job_id: str
    job_type: str
    payload: dict[str, Any]
    status: JobStatus = JobStatus.QUEUED
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: float = field(default_factory=time.time)
    finished_at: float | None = None


@runtime_checkable
class QueueBackend(Protocol):
    async def put(self, job: Job) -> None:
        ...

    async def get(self) -> Job:
        ...

    def get_job(self, job_id: str) -> Job | None:
        ...

    def update(self, job: Job) -> None:
        ...

    def size(self) -> int:
        ...


class InMemoryQueueBackend:
    """asyncio.Queue + dict job store."""

    def __init__(self, maxsize: int = 100) -> None:
        self._queue: asyncio.Queue[Job] = asyncio.Queue(maxsize=maxsize)
        self._jobs: dict[str, Job] = {}

    async def put(self, job: Job) -> None:
        self._jobs[job.job_id] = job
        await self._queue.put(job)

    async def get(self) -> Job:
        job = await self._queue.get()
        return job

    def get_job(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def update(self, job: Job) -> None:
        self._jobs[job.job_id] = job

    def size(self) -> int:
        return self._queue.qsize()


class JobQueue:
    """High-level queue facade."""

    def __init__(self, backend: QueueBackend | None = None, *, maxsize: int = 100) -> None:
        self.backend = backend or InMemoryQueueBackend(maxsize=maxsize)

    def create_job(self, job_type: str, payload: dict[str, Any]) -> Job:
        return Job(job_id=str(uuid.uuid4()), job_type=job_type, payload=payload)

    async def enqueue(self, job: Job) -> str:
        await self.backend.put(job)
        return job.job_id

    async def dequeue(self) -> Job:
        return await self.backend.get()

    def get(self, job_id: str) -> Job | None:
        return self.backend.get_job(job_id)

    def save(self, job: Job) -> None:
        self.backend.update(job)

    @property
    def size(self) -> int:
        return self.backend.size()
