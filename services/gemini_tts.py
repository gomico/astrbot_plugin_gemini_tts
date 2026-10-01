from __future__ import annotations

import base64
import tempfile
import uuid
from collections.abc import Awaitable, Callable, Mapping
from datetime import date
from pathlib import Path
from typing import Any

import httpx

UsageLogger = Callable[[str, int | None, int | None, float | None], None]
Poster = Callable[[str, dict[str, str], dict[str, Any]], Awaitable[tuple[int, Any]]]

DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com"
DEFAULT_API_VERSION = "v1beta"
DEFAULT_TIMEOUT = 120.0

_PRICE_CHANGE_DATE = date(2027, 1, 1)
_PRICES_USD_PER_MILLION = {
    "gemini-3.8-flash-tts": ((0.50, 9.00), (1.00, 18.00)),
    "gemini-3.8-flash-lite-tts": ((0.50, 6.00), (1.00, 12.00)),
}


def build_interaction_input(text: str, style: str | None) -> list[dict[str, Any]]:
    content: dict[str, Any] = {"type": "text", "text": text}
    if style is not None and str(style).strip():
        content["annotations"] = [{"type": "speech_metadata", "style": style}]
    return [{"type": "user_input", "content": [content]}]


def build_interaction_payload(
    model: str,
    text: str,
    style: str | None,
    voice: str,
) -> dict[str, Any]:
    return {
        "model": model,
        "input": build_interaction_input(text, style),
        "response_format": {"type": "audio", "mime_type": "audio/wav"},
        "generation_config": {"speech_config": [{"voice": voice}]},
    }


def _field(value: Any, name: str) -> Any:
    return value.get(name) if isinstance(value, Mapping) else getattr(value, name, None)


def interaction_token_usage(response: Any) -> tuple[int | None, int | None]:
    usage = _field(response, "usage")
    if usage is None:
        return None, None

    def token_count(*names: str) -> int | None:
        for name in names:
            value = _field(usage, name)
            if value is None:
                continue
            try:
                count = int(value)
            except (TypeError, ValueError):
                continue
            if count >= 0:
                return count
        return None

    return (
        token_count("total_input_tokens", "input_tokens"),
        token_count("total_output_tokens", "output_tokens"),
    )


def estimate_cost_usd(
    model: str,
    input_tokens: int | None,
    output_tokens: int | None,
    *,
    as_of: date | None = None,
) -> float | None:
    prices = _PRICES_USD_PER_MILLION.get(model)
    if prices is None or input_tokens is None or output_tokens is None:
        return None
    input_price, output_price = prices[1 if (as_of or date.today()) >= _PRICE_CHANGE_DATE else 0]
    return round(
        input_tokens * input_price / 1_000_000
        + output_tokens * output_price / 1_000_000,
        8,
    )


def _audio_payload(response: Any) -> Any:
    """Locate the base64 audio payload of an Interactions response.

    The HTTP response carries generated audio as an ``audio`` content block
    inside ``steps``; SDK-shaped responses expose ``output_audio.data``.
    """
    steps = _field(response, "steps")
    if isinstance(steps, (list, tuple)):
        for step in steps:
            content = _field(step, "content")
            if not isinstance(content, (list, tuple)):
                continue
            for block in content:
                if _field(block, "type") == "audio":
                    data = _field(block, "data")
                    if data:
                        return data

    output_audio = _field(response, "output_audio")
    if output_audio is not None:
        data = _field(output_audio, "data")
        if data:
            return data
    return None


def _audio_data(response: Any) -> bytes:
    data = _audio_payload(response)
    if not data:
        raise ValueError("Gemini 返回的音频数据为空")
    if isinstance(data, bytes):
        return data
    if not isinstance(data, str):
        raise ValueError("Gemini 返回了无法识别的音频数据")
    try:
        decoded = base64.b64decode(data, validate=True)
    except (ValueError, TypeError) as exc:
        raise ValueError("Gemini 返回的音频数据无效") from exc
    if not decoded:
        raise ValueError("Gemini 返回的音频数据为空")
    return decoded


def _error_message(body: Any) -> str:
    if isinstance(body, Mapping):
        error = body.get("error")
        if isinstance(error, Mapping) and error.get("message"):
            return str(error["message"])
    text = "" if body is None else str(body).strip()
    return text[:500] or "无响应内容"


def _default_poster(timeout: float) -> Poster:
    async def post(
        url: str, headers: dict[str, str], payload: dict[str, Any]
    ) -> tuple[int, Any]:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
        try:
            body: Any = response.json()
        except ValueError:
            body = response.text
        return response.status_code, body

    return post


class GeminiTTSService:
    """Calls the Gemini Interactions API directly over HTTP.

    Deliberately does not go through the ``google-genai`` SDK: the SDK's open
    union for request annotations only knows the citation variants, so
    ``speech_metadata`` — the annotation that carries ``style`` — is rewritten
    to ``UNKNOWN`` and the request is rejected with HTTP 400. Posting the
    payload ourselves keeps the plugin independent of whichever SDK version
    AstrBot Core happens to have installed.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        temp_dir: str | Path | None = None,
        poster: Poster | None = None,
        usage_logger: UsageLogger | None = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        api_version: str = DEFAULT_API_VERSION,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.api_key = str(api_key or "").strip()
        self.model = model
        self.temp_dir = Path(temp_dir or tempfile.gettempdir())
        self.base_url = str(base_url or DEFAULT_BASE_URL).rstrip("/")
        self.api_version = str(api_version or DEFAULT_API_VERSION)
        self.timeout = float(timeout)
        self._poster = poster or _default_poster(self.timeout)
        self._usage_logger = usage_logger

    @property
    def interactions_url(self) -> str:
        return f"{self.base_url}/{self.api_version}/interactions"

    async def _create_interaction(self, payload: dict[str, Any]) -> Mapping[str, Any]:
        if not self.api_key:
            raise ValueError("Gemini API Key 未配置")
        status, body = await self._poster(
            self.interactions_url,
            {"x-goog-api-key": self.api_key, "Content-Type": "application/json"},
            payload,
        )
        if status == 400:
            raise ValueError(f"Gemini 拒绝了请求 (400)：{_error_message(body)}")
        if status >= 400:
            raise RuntimeError(f"Gemini TTS 请求失败 (HTTP {status})：{_error_message(body)}")
        if not isinstance(body, Mapping):
            raise ValueError("Gemini 返回了无法识别的响应")
        return body

    async def synthesize(self, text: str, style: str | None, voice: str) -> Path:
        if not str(text or "").strip():
            raise ValueError("TTS 文本为空")
        if not str(voice or "").strip():
            raise ValueError("Gemini voice 未配置")
        response = await self._create_interaction(
            build_interaction_payload(self.model, text, style, voice)
        )
        input_tokens, output_tokens = interaction_token_usage(response)
        if self._usage_logger is not None:
            self._usage_logger(
                self.model,
                input_tokens,
                output_tokens,
                estimate_cost_usd(self.model, input_tokens, output_tokens),
            )
        data = _audio_data(response)
        try:
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            path = self.temp_dir / f"gemini-tts-{uuid.uuid4().hex}.wav"
            path.write_bytes(data)
        except OSError as exc:
            raise RuntimeError("无法创建临时 WAV 文件") from exc
        return path
