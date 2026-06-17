"""FastAPI entrypoint for the AgenticX summarizer service.

Author: Damon Li
"""

from __future__ import annotations

import argparse
import logging
from typing import Any

import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

from agenticx_service.config import AppConfig, default_config_path, load_config
from agenticx_service.summarizer import SummarizerService

logger = logging.getLogger(__name__)


class IntelliAbstractRequest(BaseModel):
    email_content: str | None = Field(default=None, description="Email or news body to summarize")


def create_app(
    config_path: str | None = None,
    *,
    config: AppConfig | None = None,
    service: SummarizerService | None = None,
) -> FastAPI:
    app_config = config or load_config(config_path or default_config_path())
    summarizer = service or SummarizerService(app_config)

    app = FastAPI(
        title="AgenticX Long Text Summarizer",
        version="1.0.0",
        description="Rich-mail intelliAbstract API backed by AgenticX",
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
            result = await summarizer.summarize(body.email_content)
        except Exception as exc:  # noqa: BLE001
            logger.exception("sid=%s summarization failed", sid)
            return JSONResponse(
                status_code=500,
                content={"code": 1, "message": str(exc), "text": ""},
            )

        logger.info(
            "sid=%s scenario=%s overflow=%s",
            sid,
            result.scenario,
            result.overflow_level,
        )
        payload: dict[str, Any] = {
            "code": 0,
            "message": "",
            "text": result.text,
            "data": {
                "scenario": result.scenario,
                "overflow_level": result.overflow_level,
            },
        }
        return JSONResponse(status_code=200, content=payload)

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
