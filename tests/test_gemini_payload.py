import asyncio
import base64
from datetime import date
from types import SimpleNamespace

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

    class Interactions:
        async def create(self, **payload):
            assert payload["response_format"]["mime_type"] == "audio/wav"
            return SimpleNamespace(
                output_audio=SimpleNamespace(data=base64.b64encode(expected).decode()),
                usage=SimpleNamespace(total_input_tokens=100, total_output_tokens=200),
            )

    class Client:
        aio = SimpleNamespace(interactions=Interactions())

    service = GeminiTTSService(
        "key",
        "gemini-3.8-flash-tts",
        tmp_path,
        lambda _: Client(),
        lambda *args: usage_logs.append(args),
    )
    path = asyncio.run(service.synthesize("hello", None, "Kore"))
    assert path.read_bytes() == expected
    assert usage_logs == [("gemini-3.8-flash-tts", 100, 200, 0.00185)]


def test_usage_tokens_and_estimated_cost():
    response = SimpleNamespace(
        usage=SimpleNamespace(total_input_tokens=1_000, total_output_tokens=2_000)
    )
    assert interaction_token_usage(response) == (1_000, 2_000)
    assert estimate_cost_usd(
        "gemini-3.8-flash-tts", 1_000, 2_000, as_of=date(2026, 10, 1)
    ) == 0.0185
