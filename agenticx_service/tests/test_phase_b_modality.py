"""Phase B multimodal ingestion smoke tests.

Author: Damon Li
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from agenticx_service.core.types import ContentPart, Modality, SummarizeRequest
from agenticx_service.factory import build_engine
from agenticx_service.modality.base import CapabilityMatrix, ModalityNotSupported, ModalityPipeline
from agenticx_service.modality.document import DocumentAdapter
from agenticx_service.modality.image import ImageAdapter
from agenticx_service.tests.conftest import make_stub_client, make_test_config


@pytest.mark.asyncio
async def test_text_passthrough() -> None:
    config = make_test_config()
    pipeline = ModalityPipeline(config)
    parts = [ContentPart(modality=Modality.TEXT, payload="hello world")]
    text, trace = await pipeline.assemble(parts, {Modality.TEXT})
    assert "hello world" in text
    assert trace == ["text"]


@pytest.mark.asyncio
async def test_code_fenced_and_truncated() -> None:
    config = make_test_config(modality={"code_max_chars": 20})
    pipeline = ModalityPipeline(config)
    parts = [
        ContentPart(
            modality=Modality.CODE,
            payload="print('x')" * 50,
            meta={"language": "python"},
        )
    ]
    text, trace = await pipeline.assemble(parts, {Modality.CODE, Modality.TEXT})
    assert "```python" in text
    assert len(text) < len("print('x')" * 50) + 20
    assert trace == ["code"]


@pytest.mark.asyncio
async def test_image_degrades_without_vision() -> None:
    config = make_test_config()
    config.llm.provider = "minimax"
    config.llm.model = "minimax-m2"
    adapter = ImageAdapter(config)
    part = ContentPart(modality=Modality.IMAGE, payload="base64payload", meta={"filename": "a.png"})
    repr_ = await adapter.to_text(part, {"config": config, "llm_client": None})
    assert "无法解析" in repr_.text or "unavailable" in repr_.text.lower()
    assert repr_.note == "vision-unavailable"


@pytest.mark.asyncio
async def test_document_adapter_uses_liteparse(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config = make_test_config()
    adapter = DocumentAdapter(config)
    doc_file = tmp_path / "report.pdf"
    doc_file.write_bytes(b"%PDF-fake")

    class FakeLiteParse:
        def is_available(self) -> bool:
            return True

        async def parse_to_text(self, file_path: Path) -> str:
            return f"parsed:{file_path.name}"

    import agenticx.tools.adapters.liteparse as liteparse_mod

    monkeypatch.setattr(liteparse_mod, "LiteParseAdapter", FakeLiteParse)
    part = ContentPart(
        modality=Modality.DOCUMENT,
        payload=str(doc_file),
        meta={"filename": "report.pdf"},
    )
    repr_ = await adapter.to_text(part, {})
    assert repr_.text.startswith("parsed:report.pdf")
    assert repr_.note == "document-liteparse"


def test_audio_video_not_supported() -> None:
    from agenticx_service.modality.audio_video import AudioVideoAdapter

    adapter = AudioVideoAdapter()
    part = ContentPart(modality=Modality.AUDIO, payload="file.wav")
    with pytest.raises(ModalityNotSupported):
        asyncio.run(adapter.to_text(part, {}))


@pytest.mark.asyncio
async def test_news_skips_unsupported_modality() -> None:
    config = make_test_config()
    pipeline = ModalityPipeline(config)
    parts = [ContentPart(modality=Modality.DOCUMENT, payload="doc body")]
    text, trace = await pipeline.assemble(parts, {Modality.TEXT, Modality.IMAGE})
    assert text == ""
    assert "skipped:document" in trace


@pytest.mark.asyncio
async def test_unsupported_modality_raises_when_asserted() -> None:
    part = ContentPart(modality=Modality.DOCUMENT, payload="doc")
    with pytest.raises(ModalityNotSupported):
        CapabilityMatrix.assert_supported(part, {Modality.TEXT})


@pytest.mark.asyncio
async def test_engine_parts_concatenated_then_summarized() -> None:
    config = make_test_config()
    engine = build_engine(config, llm_client=make_stub_client(config))
    req = SummarizeRequest(
        content="Subject: overview",
        domain="email",
        parts=[
            ContentPart(modality=Modality.CODE, payload="x=1", meta={"language": "python"}),
        ],
    )
    result = await engine.summarize(req)
    assert result.text
    modalities = result.trace.get("modalities", [])
    assert "text" in modalities
    assert "code" in modalities


@pytest.mark.asyncio
async def test_engine_with_image_placeholder() -> None:
    config = make_test_config()
    engine = build_engine(config, llm_client=make_stub_client(config))
    req = SummarizeRequest(
        content="",
        domain="news",
        parts=[ContentPart(modality=Modality.IMAGE, payload="base64...", meta={"filename": "a.png"})],
    )
    result = await engine.summarize(req)
    assert result.text
    assert "image" in result.trace.get("modalities", [])
