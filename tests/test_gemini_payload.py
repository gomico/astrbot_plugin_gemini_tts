import asyncio
import base64
from datetime import date
from types import SimpleNamespace

import pytest

from services.gemini_tts import (
    GeminiTTSService,
    build_interaction_payload,
    estimate_cost_usd,
    interaction_token_usage,
)


def test_payload_has_structured_style_and_verbatim_text():
    text = "你好<cough>世界<short pause>测试"
    payload = build_interaction_payload("gemini-3.8-flash-tts", text, "soft", "Kore")
    content = payload["input"][0]["content"][0]
    assert content["text"] == text
    assert content["annotations"] == [{"type": "speech_metadata", "style": "soft"}]
    assert payload["generation_config"] == {"speech_config": [{"voice": "Kore"}]}


def test_payload_without_style_has_no_metadata():
    payload = build_interaction_payload("gemini-3.8-flash-tts", "hello", None, "Kore")
    assert "annotations" not in payload["input"][0]["content"][0]


def test_service_writes_returned_wav_without_wrapping(tmp_path):
    expected = b"RIFF-test-wav"
    usage_logs = []
    seen = {}

    async def poster(url, headers, payload):
        seen["url"] = url
        seen["headers"] = headers
        seen["payload"] = payload
        return 200, {
            "steps": [
                {
                    "type": "model_output",
                    "content": [
                        {
                            "type": "audio",
                            "mime_type": "audio/wav",
                            "data": base64.b64encode(expected).decode(),
                        }
                    ],
                }
            ],
            "usage": {"total_input_tokens": 100, "total_output_tokens": 200},
        }

    service = GeminiTTSService(
        "key",
        "gemini-3.8-flash-tts",
        tmp_path,
        poster,
        lambda *args: usage_logs.append(args),
    )
    path = asyncio.run(service.synthesize("hello", None, "Kore"))

    assert path.read_bytes() == expected
    assert usage_logs == [("gemini-3.8-flash-tts", 100, 200, 0.00185)]
    assert seen["url"] == "https://generativelanguage.googleapis.com/v1beta/interactions"
    assert seen["headers"]["x-goog-api-key"] == "key"
    assert seen["payload"]["response_format"]["mime_type"] == "audio/wav"
    assert seen["payload"]["input"][0]["content"][0]["text"] == "hello"


def test_service_reads_sdk_shaped_output_audio(tmp_path):
    expected = b"RIFF-legacy"

    async def poster(url, headers, payload):
        return 200, {
            "output_audio": {"data": base64.b64encode(expected).decode()},
            "usage": {"total_input_tokens": 1, "total_output_tokens": 2},
        }

    service = GeminiTTSService("key", "gemini-3.8-flash-tts", tmp_path, poster)
    path = asyncio.run(service.synthesize("hello", "soft", "Kore"))
    assert path.read_bytes() == expected


def test_service_reports_http_errors(tmp_path):
    async def poster_400(url, headers, payload):
        return 400, {"error": {"message": "invalid_request: bad annotation"}}

    async def poster_500(url, headers, payload):
        return 500, {"error": {"message": "backend down"}}

    service = GeminiTTSService("key", "gemini-3.8-flash-tts", tmp_path, poster_400)
    with pytest.raises(ValueError, match="bad annotation"):
        asyncio.run(service.synthesize("hello", None, "Kore"))

    service = GeminiTTSService("key", "gemini-3.8-flash-tts", tmp_path, poster_500)
    with pytest.raises(RuntimeError, match="HTTP 500"):
        asyncio.run(service.synthesize("hello", None, "Kore"))


def test_service_requires_api_key(tmp_path):
    async def poster(url, headers, payload):  # pragma: no cover - must not be called
        raise AssertionError("poster should not be called without an API key")

    service = GeminiTTSService("", "gemini-3.8-flash-tts", tmp_path, poster)
    with pytest.raises(ValueError, match="API Key"):
        asyncio.run(service.synthesize("hello", None, "Kore"))


def test_usage_tokens_and_estimated_cost():
    response = SimpleNamespace(
        usage=SimpleNamespace(total_input_tokens=1_000, total_output_tokens=2_000)
    )
    assert interaction_token_usage(response) == (1_000, 2_000)
    assert estimate_cost_usd(
        "gemini-3.8-flash-tts", 1_000, 2_000, as_of=date(2026, 10, 1)
    ) == 0.0185
