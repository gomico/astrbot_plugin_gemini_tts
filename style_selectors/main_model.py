from __future__ import annotations

from typing import Any

try:
    from ..utils.style import normalize_style_selection
except ImportError:  # pragma: no cover - direct test/module loading fallback
    from utils.style import normalize_style_selection

from .base import StyleSelector


class MainModelStyleSelector:
    def __init__(self, context: Any) -> None:
        self.context = context

    async def select(self, event: object, text: str) -> str:
        umo = getattr(event, "unified_msg_origin", "")
        provider_id = await self.context.get_current_chat_provider_id(umo)
        response = await self.context.llm_generate(
            chat_provider_id=provider_id,
            system_prompt=(
                "Choose exactly one style key from natural, cheerful, soft, sad, "
                "excited, whispering, sarcastic, angry. Return only the key. "
                "If uncertain, return natural."
            ),
            prompt=f"Choose a voice style for this bot reply:\n{text}",
        )
        value = getattr(response, "completion_text", "")
        if not value:
            chain = getattr(response, "result_chain", None)
            getter = getattr(chain, "get_plain_text", None)
            value = getter() if callable(getter) else ""
        return normalize_style_selection(value)
