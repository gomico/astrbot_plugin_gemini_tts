from __future__ import annotations

import tempfile
from collections.abc import AsyncGenerator, Mapping
from pathlib import Path
from typing import Any

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.message_components import Record
from astrbot.api.star import Context, Star, register

try:
    from .services.gemini_tts import GeminiTTSService
    from .style_selectors.main_model import MainModelStyleSelector
    from .utils.auto import should_attempt_auto_tts
    from .utils.command_parser import parse_gemini_tts_command
    from .utils.messages import has_record, plain_text, replace_plain_components
    from .utils.style import resolve_style, style_templates
    from .utils.voice import resolve_voice
except ImportError:  # pragma: no cover - direct test/module loading fallback
    from services.gemini_tts import GeminiTTSService
    from style_selectors.main_model import MainModelStyleSelector
    from utils.auto import should_attempt_auto_tts
    from utils.command_parser import parse_gemini_tts_command
    from utils.messages import has_record, plain_text, replace_plain_components
    from utils.style import resolve_style, style_templates
    from utils.voice import resolve_voice

PLUGIN_NAME = "astrbot_plugin_gemini_tts"
MODELS = ("gemini-3.8-flash-tts", "gemini-3.8-flash-lite-tts")
_SKIP_AUTO = f"{PLUGIN_NAME}:skip_auto"
_AUTO_ATTEMPTED = f"{PLUGIN_NAME}:auto_attempted"
_AUTO_PROCESSING = f"{PLUGIN_NAME}:auto_processing"


def _temp_dir() -> Path:
    try:
        from astrbot.core.utils.astrbot_path import get_astrbot_temp_path

        return Path(get_astrbot_temp_path()) / PLUGIN_NAME
    except (ImportError, AttributeError):  # pragma: no cover - test fallback
        return Path(tempfile.gettempdir()) / PLUGIN_NAME


@register(
    PLUGIN_NAME,
    "gomico",
    "直接调用 Gemini 3.8 TTS，支持 voice、style、inline vocal tags 和自动语音回复。",
    "0.1.0",
)
class GeminiTTSPlugin(Star):
    def __init__(self, context: Context, config: Mapping[str, Any]):
        super().__init__(context)
        self.context = context
        self.config = config
        self.enabled = bool(config.get("enabled", True))
        self.tool_enabled = bool(config.get("tool_enabled", True))
        self.auto_enabled = bool(config.get("auto_tts_enabled", False))
        self.auto_probability = float(config.get("auto_tts_probability", 0.15) or 0)
        model = str(config.get("model", MODELS[0]))
        if model not in MODELS:
            logger.warning("Gemini TTS model 配置无效，回退默认模型")
            model = MODELS[0]

        self.styles = style_templates(config.get("style_templates"))
        self.voice = resolve_voice(
            str(config.get("prebuilt_voice", "Kore")),
            str(config.get("voice_id_override", "")),
            str(config.get("custom_voice_alias", "")),
            config.get("custom_voice_aliases"),
        )
        self.service = GeminiTTSService(
            str(config.get("api_key", "")),
            model,
            _temp_dir(),
            usage_logger=self._log_usage,
        )
        self.style_selector = MainModelStyleSelector(context)

    @staticmethod
    def _log_usage(
        model: str,
        input_tokens: int | None,
        output_tokens: int | None,
        estimated_price_usd: float | None,
    ) -> None:
        price = "unknown" if estimated_price_usd is None else f"{estimated_price_usd:.8f}"
        logger.info(
            "Gemini TTS usage: model=%s input_tokens=%s output_tokens=%s estimated_price_usd=%s",
            model,
            input_tokens if input_tokens is not None else "unknown",
            output_tokens if output_tokens is not None else "unknown",
            price,
        )

    @staticmethod
    def _extra(event: AstrMessageEvent, key: str, default: Any = False) -> Any:
        getter = getattr(event, "get_extra", None)
        return getter(key, default) if callable(getter) else default

    @staticmethod
    def _set_extra(event: AstrMessageEvent, key: str, value: Any = True) -> None:
        setter = getattr(event, "set_extra", None)
        if callable(setter):
            setter(key, value)

    @staticmethod
    def _track_file(event: AstrMessageEvent, path: Path) -> None:
        tracker = getattr(event, "track_temporary_local_file", None)
        if callable(tracker):
            tracker(str(path))

    @staticmethod
    def _friendly_error(exc: Exception) -> str:
        if isinstance(exc, ValueError):
            return "Gemini TTS 配置或响应无效，请检查文本、voice 和 API 响应。"
        return "Gemini TTS 请求失败，请检查 API Key、配额、网络和 voice 配置。"

    async def _synthesize(self, text: str, style: str | None) -> Path:
        return await self.service.synthesize(text, style, self.voice)

    @staticmethod
    def _record(path: Path, text: str) -> Any:
        return Record.fromFileSystem(str(path), text=text)

    @filter.command("GEMINITTS")
    async def gemini_tts_command(self, event: AstrMessageEvent) -> AsyncGenerator[Any, None]:
        self._set_extra(event, _SKIP_AUTO)
        text, requested_style = parse_gemini_tts_command(event.message_str)
        if not text.strip():
            yield event.plain_result("用法：/GEMINITTS <text>&&<style>，style 可省略")
            return
        if not self.enabled:
            yield event.plain_result("Gemini TTS 插件未启用")
            return

        style = resolve_style(requested_style, self.styles, empty_behavior="none")
        try:
            path = await self._synthesize(text, style)
            self._track_file(event, path)
            self._set_extra(event, _AUTO_ATTEMPTED)
            yield event.chain_result([self._record(path, text)])
        except Exception as exc:
            logger.warning("Gemini TTS command failed (%s)", type(exc).__name__)
            yield event.plain_result(self._friendly_error(exc))

    @filter.llm_tool(name="gemini_tts")
    async def gemini_tts(self, event: AstrMessageEvent, text: str = "", style: str = "") -> str:
        """使用 Gemini TTS 生成并发送语音。

        Args:
            text(string): 要逐字朗读的文本，可包含 Gemini point-in-time inline vocal tags。
            style(string): 朗读语气或 style preset，可为空；为空时使用 natural preset。
        """
        self._set_extra(event, _SKIP_AUTO)
        if not self.enabled or not self.tool_enabled:
            return "Gemini TTS Tool 未启用"
        if not str(text or "").strip():
            return "语音文本为空"

        resolved_style = resolve_style(style, self.styles, empty_behavior="natural")
        try:
            path = await self._synthesize(text, resolved_style)
            self._track_file(event, path)
            await event.send(event.chain_result([self._record(path, text)]))
            self._set_extra(event, _AUTO_ATTEMPTED)
            return "语音已发送"
        except Exception as exc:
            logger.warning("Gemini TTS tool failed (%s)", type(exc).__name__)
            return self._friendly_error(exc)

    @filter.on_decorating_result(priority=14)
    async def on_decorating_result(self, event: AstrMessageEvent) -> None:
        if not self.auto_enabled:
            return
        if self._extra(event, _SKIP_AUTO) or self._extra(event, _AUTO_ATTEMPTED):
            return
        if self._extra(event, _AUTO_PROCESSING):
            return

        result = event.get_result()
        chain = getattr(result, "chain", None) if result else None
        if not chain or has_record(chain):
            return
        is_llm_result = getattr(result, "is_llm_result", None)
        if callable(is_llm_result) and not is_llm_result():
            return

        transcript = plain_text(chain)
        if not should_attempt_auto_tts(
            True,
            self.auto_probability,
            readable_text=bool(transcript and transcript.strip()),
            already_processed=False,
        ):
            return

        self._set_extra(event, _AUTO_PROCESSING)
        try:
            preset = await self.style_selector.select(event, transcript or "")
            style = resolve_style(preset, self.styles, empty_behavior="natural")
            path = await self._synthesize(transcript or "", style)
            record = self._record(path, transcript or "")
            if replace_plain_components(chain, record):
                self._track_file(event, path)
                self._set_extra(event, _AUTO_ATTEMPTED)
        except Exception as exc:
            logger.warning("Gemini auto TTS failed (%s)", type(exc).__name__)
        finally:
            self._set_extra(event, _AUTO_PROCESSING, False)
