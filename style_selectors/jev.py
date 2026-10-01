from __future__ import annotations

import asyncio
import json
import math
from collections.abc import Iterable, Mapping
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

try:
    from ..utils.style import STYLE_PRESETS, normalize_style_selection
except ImportError:  # pragma: no cover - direct test/module loading fallback
    from utils.style import STYLE_PRESETS, normalize_style_selection

from .base import StyleSelector


DEFAULT_JEV_BASE_URL = "https://api.typesafe.ai"
DEFAULT_JEV_MODEL = "jev-latest"
DEFAULT_JEV_CONFIDENCE_THRESHOLD = 0.7
DEFAULT_JEV_STYLES = tuple(
    style for style in STYLE_PRESETS if style not in {"whispering", "sarcastic"}
)
JEV_STYLE_DESCRIPTIONS = {
    "natural": "Neutral, informational, conversational, or emotionally ambiguous.",
    "cheerful": "Positive, friendly, welcoming, or playful.",
    "soft": "Comforting, gentle, caring, calm, or reassuring.",
    "sad": "Sad, disappointed, regretful, subdued, or low-spirited.",
    "excited": "Strong anticipation, surprise, enthusiasm, or high energy.",
    "whispering": "The text clearly calls for a quiet, secretive, or hushed delivery.",
    "sarcastic": "The text clearly uses irony, mockery, dry humor, or teasing.",
    "angry": "Anger, accusation, hostility, frustration, or forceful dissatisfaction.",
}


def normalize_jev_styles(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        values: Iterable[object] = value.split(",")
    elif isinstance(value, Iterable) and not isinstance(
        value, (bytes, bytearray, Mapping)
    ):
        values = value
    else:
        values = ()

    selected = tuple(
        dict.fromkeys(
            style
            for style in (str(item).strip().lower() for item in values)
            if style in STYLE_PRESETS
        )
    )
    if not selected:
        selected = DEFAULT_JEV_STYLES
    if "natural" not in selected:
        selected = ("natural", *selected)
    return selected


def build_jev_payload(text: str, styles: Iterable[str], model: str) -> dict[str, Any]:
    return {
        "model": model,
        "state": text,
        "questions": {
            "style": {
                "type": "choice",
                "instructions": (
                    "Choose the single best speaking style for this bot reply. "
                    "Choose natural when the style is unclear or no strong emotion is present."
                ),
                "criteria": {
                    style: JEV_STYLE_DESCRIPTIONS[style]
                    for style in styles
                    if style in JEV_STYLE_DESCRIPTIONS
                },
            }
        },
    }


def parse_jev_style(
    response: Mapping[str, Any],
    styles: Iterable[str],
    confidence_threshold: float,
) -> str:
    allowed = set(styles)
    answers = response.get("answers")
    if not isinstance(answers, Mapping):
        return "natural"
    answer = answers.get("style", {})
    if not isinstance(answer, Mapping):
        return "natural"

    choice = normalize_style_selection(answer.get("choice"))
    try:
        confidence = float(answer.get("confidence"))
    except (TypeError, ValueError):
        return "natural"

    if (
        choice not in allowed
        or not math.isfinite(confidence)
        or confidence < confidence_threshold
    ):
        return "natural"
    return choice


def _systemone_url(base_url: str) -> str:
    value = str(base_url or "").strip().rstrip("/")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Jev base URL 必须是 http 或 https 地址")
    if value.endswith("/v1/systemone"):
        return value
    if value.endswith("/v1"):
        return f"{value}/systemone"
    return f"{value}/v1/systemone"


def _post_json(url: str, api_key: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            body = response.read(1_000_000)
    except HTTPError as exc:
        raise RuntimeError(f"Jev 请求失败（HTTP {exc.code}）") from exc
    except URLError as exc:
        raise RuntimeError("Jev 请求失败，请检查网络和 base URL") from exc

    result = json.loads(body)
    if not isinstance(result, Mapping):
        raise ValueError("Jev 返回了无法识别的响应")
    return result


class JevStyleSelector:
    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_JEV_BASE_URL,
        model: str = DEFAULT_JEV_MODEL,
        styles: object = None,
        confidence_threshold: float = DEFAULT_JEV_CONFIDENCE_THRESHOLD,
    ) -> None:
        self.api_key = str(api_key or "").strip()
        self.url = _systemone_url(base_url or DEFAULT_JEV_BASE_URL)
        self.model = str(model or DEFAULT_JEV_MODEL).strip()
        self.styles = normalize_jev_styles(styles)
        self.confidence_threshold = min(1.0, max(0.0, float(confidence_threshold)))

    async def select(self, event: object, text: str) -> str:
        if not self.api_key:
            raise ValueError("Jev API Key 未配置")
        payload = build_jev_payload(text, self.styles, self.model)
        response = await asyncio.to_thread(_post_json, self.url, self.api_key, payload)
        return parse_jev_style(response, self.styles, self.confidence_threshold)
