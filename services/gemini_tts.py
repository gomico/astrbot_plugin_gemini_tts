from __future__ import annotations

import asyncio
import base64
import inspect
import tempfile
import uuid
from collections.abc import Callable, Mapping
from datetime import date
from pathlib import Path
from typing import Any


UsageLogger = Callable[[str, int | None, int | None, float | None], None]
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


def _audio_data(response: Any) -> bytes:
    output_audio = response.get("output_audio") if isinstance(response, Mapping) else getattr(response, "output_audio", None)
    data = output_audio.get("data") if isinstance(output_audio, Mapping) else getattr(output_audio, "data", None)
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


class GeminiTTSService:
    def __init__(
        self,
        api_key: str,
        model: str,
        temp_dir: str | Path | None = None,
        client_factory: Callable[[str], Any] | None = None,
        usage_logger: UsageLogger | None = None,
    ) -> None:
        self.api_key = str(api_key or "").strip()
        self.model = model
        self.temp_dir = Path(temp_dir or tempfile.gettempdir())
        self._client_factory = client_factory
        self._usage_logger = usage_logger
        self._client: Any | None = None

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        if not self.api_key:
            raise ValueError("Gemini API Key 未配置")
        if self._client_factory is None:
            try:
                from google import genai
            except ImportError as exc:
                raise RuntimeError("未安装 google-genai 依赖") from exc
            self._client = genai.Client(api_key=self.api_key)
        else:
            self._client = self._client_factory(self.api_key)
        return self._client

    async def _create_interaction(self, payload: dict[str, Any]) -> Any:
        client = self._get_client()
        interactions = getattr(getattr(client, "aio", None), "interactions", None)
        create = getattr(interactions, "create", None)
        if create is not None:
            if inspect.iscoroutinefunction(create):
                return await create(**payload)
            result = await asyncio.to_thread(create, **payload)
            return await result if inspect.isawaitable(result) else result

        create = getattr(getattr(client, "interactions", None), "create", None)
        if create is None:
            raise RuntimeError("google-genai Client 不支持 Interactions API")
        result = await asyncio.to_thread(create, **payload)
        return await result if inspect.isawaitable(result) else result

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
