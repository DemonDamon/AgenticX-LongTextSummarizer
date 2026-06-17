"""FastAPI HTTP layer smoke tests.

Author: Damon Li
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from agenticx_service.app import create_app
from agenticx_service.summarizer import SummarizerService
from agenticx_service.tests.conftest import make_stub_client, make_test_config


def _client() -> TestClient:
    config = make_test_config()
    service = SummarizerService(config, llm_client=make_stub_client(config))
    return TestClient(create_app(config=config, service=service))


def test_intelli_abstract_missing_sid() -> None:
    response = _client().post(
        "/aibox/richMail/v1.0/intelliAbstract",
        json={"email_content": "hello"},
    )
    assert response.status_code == 400
    body = response.json()
    assert body["code"] == 1
    assert "sid" in body["message"]


def test_intelli_abstract_missing_email_content() -> None:
    response = _client().post(
        "/aibox/richMail/v1.0/intelliAbstract?sid=demo",
        json={},
    )
    assert response.status_code == 400
    body = response.json()
    assert body["code"] == 1
    assert "email_content" in body["message"]


def test_intelli_abstract_success_shape() -> None:
    response = _client().post(
        "/aibox/richMail/v1.0/intelliAbstract?sid=demo",
        json={"email_content": "Subject: Sync\nPlease confirm Friday attendance."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["text"]
    assert body["data"]["scenario"] == "email"
    assert body["data"]["overflow_level"] >= 1
