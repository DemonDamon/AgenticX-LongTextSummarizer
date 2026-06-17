"""Sanic API entrypoint for the AgenticX summarizer service.

Author: Damon Li
"""

from __future__ import annotations

import argparse
import logging

from sanic import Sanic
from sanic.response import json
from sanic_cors import CORS

from agenticx_service.config import default_config_path, load_config
from agenticx_service.summarizer import SummarizerService

logger = logging.getLogger(__name__)


def create_app(config_path: str | None = None) -> Sanic:
    app = Sanic("agenticx_longtext_summarizer")
    CORS(app, origins="*")

    config = load_config(config_path or default_config_path())
    service = SummarizerService(config)

    @app.post("/aibox/richMail/v1.0/intelliAbstract")
    async def intelli_abstract(request):
        sid_id = request.args.get("sid")
        if not sid_id:
            logger.error("sid is missing")
            return json(
                {"code": 1, "message": "'sid' is None", "text": "", "data": []},
                status=400,
            )

        body = request.json or {}
        if "email_content" not in body:
            logger.error("sid=%s missing email_content", sid_id)
            return json(
                {
                    "code": 1,
                    "message": "Invalid request: 'email_content' missing",
                    "text": "",
                },
                status=400,
            )

        try:
            result = await service.summarize(body["email_content"])
        except Exception as exc:  # noqa: BLE001
            logger.exception("sid=%s summarization failed", sid_id)
            return json(
                {"code": 1, "message": str(exc), "text": ""},
                status=500,
            )

        logger.info("sid=%s scenario=%s overflow=%s", sid_id, result.scenario, result.overflow_level)
        return json(
            {
                "code": 0,
                "message": "",
                "text": result.text,
                "data": {
                    "scenario": result.scenario,
                    "overflow_level": result.overflow_level,
                },
            }
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
    app = create_app(args.config)
    app.run(host=config.server.host, port=config.server.port, debug=False)


if __name__ == "__main__":
    main()
