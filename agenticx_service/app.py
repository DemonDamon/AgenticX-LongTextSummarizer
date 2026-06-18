"""FastAPI entrypoint for the AgenticX summarizer service.

Author: Damon Li
"""

from __future__ import annotations

import argparse
import logging
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

from agenticx.core.token_counter import count_tokens

from agenticx_service.agentic.personalization import PersonalizationStore
from agenticx_service.batch.queue import JobQueue, JobStatus
from agenticx_service.batch.resource import CapacityGuard, ResourceEstimator
from agenticx_service.batch.worker import SummaryWorker
from agenticx_service.config import AppConfig, default_config_path, load_config
from agenticx_service.core.engine import SummarizationEngine
from agenticx_service.core.types import ContentPart, Modality, SummarizeRequest
from agenticx_service.factory import build_engine
from agenticx_service.multidoc.collection import CollectionSummarizer
from agenticx_service.multidoc.types import CollectionIntent, CollectionRequest, DocInput
from agenticx_service.summarizer import SummarizerService

logger = logging.getLogger(__name__)


class IntelliAbstractRequest(BaseModel):
    email_content: str | None = Field(default=None, description="Email or news body to summarize")


class PartModel(BaseModel):
    modality: str
    payload: str
    meta: dict[str, Any] = Field(default_factory=dict)


class V2SummarizeRequest(BaseModel):
    content: str
    domain: str | None = None
    user_id: str | None = None
    parts: list[PartModel] | None = None
    options: dict[str, Any] = Field(default_factory=dict)


class BatchItem(BaseModel):
    content: str
    domain: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)


class BatchRequest(BaseModel):
    items: list[BatchItem]


class DocInputModel(BaseModel):
    doc_id: str
    title: str | None = None
    content: str
    domain: str | None = None
    parts: list[PartModel] | None = None


class CollectionBody(BaseModel):
    docs: list[DocInputModel]
    intent: str = "aggregate"
    options: dict[str, Any] = Field(default_factory=dict)


class FeedbackBody(BaseModel):
    user_id: str
    domain: str
    instruction: str


def _parts_from_models(parts: list[PartModel] | None) -> list[ContentPart] | None:
    if not parts:
        return None
    return [
        ContentPart(modality=Modality(p.modality), payload=p.payload, meta=p.meta)
        for p in parts
    ]


def _summarize_request(body: V2SummarizeRequest) -> SummarizeRequest:
    options = dict(body.options)
    if body.user_id:
        options["user_id"] = body.user_id
    return SummarizeRequest(
        content=body.content,
        domain=body.domain,
        parts=_parts_from_models(body.parts),
        options=options,
    )


def create_app(
    config_path: str | None = None,
    *,
    config: AppConfig | None = None,
    service: SummarizerService | None = None,
    engine: SummarizationEngine | None = None,
) -> FastAPI:
    app_config = config or load_config(config_path or default_config_path())
    summarizer = service or SummarizerService(app_config)
    summarization_engine = engine or summarizer.engine
    job_queue = JobQueue(maxsize=app_config.batch.queue_max)
    worker = SummaryWorker(app_config, job_queue, summarization_engine)
    collection = CollectionSummarizer(app_config, summarization_engine)
    estimator = ResourceEstimator(app_config)
    capacity = CapacityGuard(app_config)
    personalization = PersonalizationStore(app_config)

    @asynccontextmanager
    async def lifespan(app: FastAPI):  # noqa: ARG001
        await worker.start()
        yield
        await worker.stop()

    app = FastAPI(
        title="AgenticX Long Text Summarizer",
        version="2.0.0",
        description="Rich-mail intelliAbstract + v2 summarize API backed by AgenticX",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.config = app_config
    app.state.summarizer = summarizer
    app.state.engine = summarization_engine
    app.state.job_queue = job_queue
    app.state.worker = worker
    app.state.collection = collection
    app.state.estimator = estimator
    app.state.capacity = capacity
    app.state.personalization = personalization

    @app.post("/aibox/richMail/v1.0/intelliAbstract")
    async def intelli_abstract(
        body: IntelliAbstractRequest,
        sid: str | None = Query(default=None),
    ) -> JSONResponse:
        if not sid:
            logger.error("sid is missing")
            return JSONResponse(
                status_code=400,
                content={"code": 1, "message": "'sid' is None", "text": "", "data": []},
            )

        if not body.email_content:
            logger.error("sid=%s missing email_content", sid)
            return JSONResponse(
                status_code=400,
                content={
                    "code": 1,
                    "message": "Invalid request: 'email_content' missing",
                    "text": "",
                },
            )

        try:
            result = await summarization_engine.summarize(
                SummarizeRequest(content=body.email_content)
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("sid=%s summarization failed", sid)
            return JSONResponse(
                status_code=500,
                content={"code": 1, "message": str(exc), "text": ""},
            )

        logger.info(
            "sid=%s scenario=%s overflow=%s",
            sid,
            result.domain,
            result.overflow_level,
        )
        payload: dict[str, Any] = {
            "code": 0,
            "message": "",
            "text": result.text,
            "data": {
                "scenario": result.domain,
                "overflow_level": result.overflow_level,
            },
        }
        return JSONResponse(status_code=200, content=payload)

    @app.post("/v2/summarize")
    async def v2_summarize(body: V2SummarizeRequest) -> JSONResponse:
        try:
            result = await summarization_engine.summarize(_summarize_request(body))
        except ValueError as exc:
            return JSONResponse(
                status_code=400,
                content={"code": 1, "message": str(exc), "text": "", "data": {}},
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("v2 summarize failed")
            return JSONResponse(
                status_code=500,
                content={"code": 1, "message": str(exc), "text": "", "data": {}},
            )
        return JSONResponse(
            status_code=200,
            content={
                "code": 0,
                "message": "",
                "text": result.text,
                "data": {
                    "domain": result.domain,
                    "overflow_level": result.overflow_level,
                    "trace": result.trace,
                },
            },
        )

    @app.post("/v2/summarize/batch")
    async def v2_batch(body: BatchRequest) -> JSONResponse:
        responses: list[dict[str, Any]] = []
        token_counts = [
            count_tokens(item.content, model=app_config.llm.model) for item in body.items
        ]
        batch_estimate = estimator.estimate_batch(token_counts)
        for item in body.items:
            tokens = count_tokens(item.content, model=app_config.llm.model)
            estimate = estimator.estimate_single(tokens)
            decision = capacity.decide(estimate, worker.in_flight, job_queue.size)
            payload = {
                "content": item.content,
                "domain": item.domain,
                "options": item.options,
            }
            if decision == "reject":
                responses.append(
                    {"status": "rejected", "reason": "capacity exceeded", "content": item.content[:80]}
                )
                continue
            if decision == "enqueue":
                job = job_queue.create_job("summarize", payload)
                await job_queue.enqueue(job)
                responses.append({"status": "queued", "job_id": job.job_id})
                continue
            try:
                result = await summarization_engine.summarize(
                    SummarizeRequest(
                        content=item.content,
                        domain=item.domain,
                        options=item.options,
                    )
                )
                responses.append(
                    {
                        "status": "done",
                        "result": {
                            "text": result.text,
                            "domain": result.domain,
                            "overflow_level": result.overflow_level,
                            "trace": result.trace,
                        },
                    }
                )
            except Exception as exc:  # noqa: BLE001
                responses.append({"status": "failed", "error": str(exc)})
        return JSONResponse(
            status_code=200,
            content={
                "code": 0,
                "message": "",
                "data": {
                    "items": responses,
                    "batch_estimate": {
                        "calls": batch_estimate.calls,
                        "est_latency_s": batch_estimate.est_latency_s,
                        "required_rpm": batch_estimate.required_rpm,
                        "required_tpm": batch_estimate.required_tpm,
                    },
                },
            },
        )

    @app.get("/v2/jobs/{job_id}")
    async def get_job(job_id: str) -> JSONResponse:
        job = job_queue.get(job_id)
        if job is None:
            return JSONResponse(
                status_code=404,
                content={"code": 1, "message": "job not found", "data": {}},
            )
        return JSONResponse(
            status_code=200,
            content={
                "code": 0,
                "message": "",
                "data": {
                    "job_id": job.job_id,
                    "status": job.status.value,
                    "result": job.result,
                    "error": job.error,
                    "created_at": job.created_at,
                    "finished_at": job.finished_at,
                },
            },
        )

    @app.post("/v2/summarize/collection")
    async def v2_collection(body: CollectionBody) -> JSONResponse:
        docs = [
            DocInput(
                doc_id=d.doc_id,
                title=d.title,
                content=d.content,
                domain=d.domain,
                parts=_parts_from_models(d.parts),
            )
            for d in body.docs
        ]
        request = CollectionRequest(
            docs=docs,
            intent=CollectionIntent(body.intent),
            options=body.options,
        )
        total_tokens = sum(
            count_tokens(d.content, model=app_config.llm.model) for d in docs
        )
        estimate = estimator.estimate_batch([total_tokens // max(len(docs), 1)] * len(docs))
        large = len(docs) > app_config.multidoc.sync_max_docs or estimate.calls > 20
        if large:
            job = job_queue.create_job(
                "collection",
                {
                    "docs": [
                        {
                            "doc_id": d.doc_id,
                            "title": d.title,
                            "content": d.content,
                            "domain": d.domain,
                        }
                        for d in docs
                    ],
                    "intent": body.intent,
                    "options": body.options,
                },
            )
            await job_queue.enqueue(job)
            return JSONResponse(
                status_code=202,
                content={
                    "code": 0,
                    "message": "queued",
                    "data": {"job_id": job.job_id, "status": JobStatus.QUEUED.value},
                },
            )
        try:
            result = await collection.summarize(request)
        except Exception as exc:  # noqa: BLE001
            logger.exception("collection failed")
            return JSONResponse(
                status_code=500,
                content={"code": 1, "message": str(exc), "data": {}},
            )
        return JSONResponse(status_code=200, content={"code": 0, "message": "", "data": result.to_dict()})

    @app.post("/v2/feedback")
    async def v2_feedback(body: FeedbackBody) -> JSONResponse:
        await personalization.record_feedback(body.user_id, body.domain, body.instruction)
        return JSONResponse(
            status_code=200,
            content={"code": 0, "message": "recorded", "data": {}},
        )

    return app


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default=str(default_config_path()),
        help="Path to config_agenticx.yaml",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    config = load_config(args.config)
    app = create_app(config=config)
    uvicorn.run(app, host=config.server.host, port=config.server.port, log_level="info")


if __name__ == "__main__":
    main()
