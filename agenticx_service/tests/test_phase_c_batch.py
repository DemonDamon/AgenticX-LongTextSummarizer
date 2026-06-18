"""Phase C batch/resource/queue smoke tests.

Author: Damon Li
"""

from __future__ import annotations

import asyncio
import time

import pytest
from fastapi.testclient import TestClient

from agenticx_service.app import create_app
from agenticx_service.batch.queue import JobQueue
from agenticx_service.batch.resource import CapacityGuard, ResourceEstimator
from agenticx_service.batch.worker import SummaryWorker
from agenticx_service.factory import build_engine
from agenticx_service.tests.conftest import make_stub_client, make_test_config


def test_estimate_single_pass_vs_mapreduce() -> None:
    config = make_test_config(chunking={"max_single_pass_tokens": 100, "chunk_size": 50})
    estimator = ResourceEstimator(config)
    short = estimator.estimate_single(50, config)
    long = estimator.estimate_single(500, config)
    assert short.calls == 1
    assert short.n_chunks == 1
    assert long.calls > 1
    assert long.n_chunks == max(1, (500 + 49) // 50)


def test_estimate_batch_scales() -> None:
    config = make_test_config()
    estimator = ResourceEstimator(config)
    single = estimator.estimate_single(500, config)
    batch = estimator.estimate_batch([500, 500], config)
    assert batch.calls >= single.calls * 2

    low_concurrency = make_test_config(batch={"batch_concurrency": 1})
    high_concurrency = make_test_config(batch={"batch_concurrency": 4})
    batch_low = estimator.estimate_batch([500, 500], low_concurrency)
    batch_high = estimator.estimate_batch([500, 500], high_concurrency)
    assert batch_high.est_latency_s <= batch_low.est_latency_s


def test_capacity_guard_enqueue_when_over_limit() -> None:
    config = make_test_config(batch={"inline_max_concurrency": 0, "queue_max": 10})
    guard = CapacityGuard(config)
    estimator = ResourceEstimator(config)
    estimate = estimator.estimate_single(100, config)
    assert guard.decide(estimate, in_flight=0, queue_size=0) == "enqueue"
    assert guard.decide(estimate, in_flight=1, queue_size=10) == "reject"


def test_batch_inline_path() -> None:
    config = make_test_config(
        batch={
            "inline_max_concurrency": 10,
            "provider_rpm_limit": 9999,
            "provider_tpm_limit": 999_999,
        }
    )
    engine = build_engine(config, llm_client=make_stub_client(config))
    with TestClient(create_app(config=config, engine=engine)) as client:
        response = client.post(
            "/v2/summarize/batch",
            json={
                "items": [
                    {"content": "Subject: batch-a\nPlease confirm."},
                    {"content": "Subject: batch-b\nPlease confirm."},
                ]
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    items = body["data"]["items"]
    assert len(items) == 2
    assert all(item["status"] == "done" for item in items)
    assert all(item["result"]["text"] for item in items)
    assert body["data"]["batch_estimate"]["calls"] >= 2


@pytest.mark.asyncio
async def test_queue_worker_consumes_job() -> None:
    config = make_test_config(batch={"batch_concurrency": 1})
    engine = build_engine(config, llm_client=make_stub_client(config))
    queue = JobQueue(maxsize=10)
    worker = SummaryWorker(config, queue, engine)
    await worker.start()
    job = queue.create_job("summarize", {"content": "Subject: hello", "domain": "email"})
    await queue.enqueue(job)
    for _ in range(50):
        await asyncio.sleep(0.05)
        saved = queue.get(job.job_id)
        if saved and saved.status.value in {"done", "failed"}:
            break
    await worker.stop()
    saved = queue.get(job.job_id)
    assert saved is not None
    assert saved.status.value == "done"
    assert saved.result and saved.result.get("text")


def test_jobs_endpoint_returns_status() -> None:
    config = make_test_config(
        batch={
            "inline_max_concurrency": 0,
            "queue_max": 10,
            "batch_concurrency": 1,
        }
    )
    engine = build_engine(config, llm_client=make_stub_client(config))
    with TestClient(create_app(config=config, engine=engine)) as client:
        batch_resp = client.post(
            "/v2/summarize/batch",
            json={"items": [{"content": "Subject: queued job test"}]},
        )
        assert batch_resp.status_code == 200
        item = batch_resp.json()["data"]["items"][0]
        assert item["status"] == "queued"
        job_id = item["job_id"]

        status = "queued"
        for _ in range(50):
            job_resp = client.get(f"/v2/jobs/{job_id}")
            assert job_resp.status_code == 200
            data = job_resp.json()["data"]
            assert data["job_id"] == job_id
            status = data["status"]
            if status in {"done", "failed"}:
                break
            time.sleep(0.05)

        assert status == "done"
        final = client.get(f"/v2/jobs/{job_id}").json()["data"]
        assert final["result"] and final["result"].get("text")
