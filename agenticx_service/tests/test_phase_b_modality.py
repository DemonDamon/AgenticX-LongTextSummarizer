"""Phase B multimodal ingestion smoke tests.

Author: Damon Li
"""

from __future__ import annotations

import pytest

from agenticx_service.core.types import ContentPart, Modality, SummarizeRequest
from agenticx_service.factory import build_engine
from agenticx_service.modality.base import CapabilityMatrix, ModalityPipeline
from agenticx_service.tests.conftest import make_stub_client, make_test_config


@pytest.mark.asyncio
async def test_text_adapter_passthrough() -> None:
    config = make_test_config()
    pipeline = ModalityPipeline(config)
    parts = [ContentPart(modality=Modality.TEXT, payload="hello world")]
    text, trace = await pipeline.assemble(parts, {Modality.TEXT})
    assert "hello world" in text
    assert trace == ["text"]


@pytest.mark.asyncio
async def test_code_adapter_fences() -> None:
    config = make_test_config()
    pipeline = ModalityPipeline(config)
    parts = [ContentPart(modality=Modality.CODE, payload="print('x')", meta={"language": "python"})]
    text, trace = await pipeline.assemble(parts, {Modality.CODE, Modality.TEXT})
    assert "```python" in text
    assert trace == ["code"]


@pytest.mark.asyncio
async def test_unsupported_modality_rejected() -> None:
    part = ContentPart(modality=Modality.DOCUMENT, payload="doc")
    with pytest.raises(ValueError):
        CapabilityMatrix.assert_supported(part, {Modality.TEXT})


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


def test_audio_video_not_supported() -> None:
    from agenticx_service.modality.audio_video import AudioVideoAdapter, AudioVideoNotSupportedError

    adapter = AudioVideoAdapter()
    part = ContentPart(modality=Modality.AUDIO, payload="file.wav")
    with pytest.raises(AudioVideoNotSupportedError):
        import asyncio

        asyncio.run(adapter.to_text(part, {}))
