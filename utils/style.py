from __future__ import annotations

from collections.abc import Mapping

STYLE_PRESETS = (
    "natural", "cheerful", "soft", "sad", "excited", "whispering", "sarcastic", "angry",
)

DEFAULT_STYLE_TEMPLATES = {
    "natural": "natural, conversational, and relaxed",
    "cheerful": "cheerful, bright, and friendly",
    "soft": "soft, gentle, calm, and warm",
    "sad": "sad, subdued, and emotionally restrained",
    "excited": "excited, energetic, and enthusiastic",
    "whispering": "whispering softly",
    "sarcastic": "sarcastic, dry, and slightly teasing",
    "angry": "angry, tense, and forceful",
}


def style_templates(value: Mapping[str, object] | None) -> dict[str, str]:
    result = DEFAULT_STYLE_TEMPLATES.copy()
    if isinstance(value, Mapping):
        for name in STYLE_PRESETS:
            if name in value:
                result[name] = str(value[name] or "")
    return result


def resolve_style(
    style: str | None,
    templates: Mapping[str, str] | None = None,
    *,
    empty_behavior: str = "none",
) -> str | None:
    """Resolve a preset while preserving unknown styles verbatim."""
    if style is None or not str(style).strip():
        return style_templates(templates)["natural"] if empty_behavior == "natural" else None
    value = str(style)
    return style_templates(templates)[value] if value in STYLE_PRESETS else value


def normalize_style_selection(value: object) -> str:
    candidate = str(value or "").strip().lower()
    return candidate if candidate in STYLE_PRESETS else "natural"
