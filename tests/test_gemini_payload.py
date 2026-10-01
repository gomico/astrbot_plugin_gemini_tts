import asyncio
import base64
from types import SimpleNamespace

from services.gemini_tts import GeminiTTSService, build_interaction_payload


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

    class Interactions:
        async def create(self, **payload):
            assert payload["response_format"]["mime_type"] == "audio/wav"
            return SimpleNamespace(
                output_audio=SimpleNamespace(data=base64.b64encode(expected).decode())
            )

    class Client:
        aio = SimpleNamespace(interactions=Interactions())

    service = GeminiTTSService("key", "gemini-3.8-flash-tts", tmp_path, lambda _: Client())
    path = asyncio.run(service.synthesize("hello", None, "Kore"))
    assert path.read_bytes() == expected
