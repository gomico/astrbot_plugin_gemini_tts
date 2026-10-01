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
DEFAULT_LANGUAGE_GUIDANCE = (
    "Speak in the language of the input text.\n"
    "For Mandarin Chinese, use Mainland Standard Mandarin (zh-CN), "
    "not Taiwanese or Singaporean Mandarin.\n"
    "For Japanese, use standard Japanese (Tokyo dialect).\n"
    "For English, use British English with a Received Pronunciation accent.\n"
    "Do not translate or switch languages unless explicitly requested."
)


def style_templates(value: Mapping[str, object] | None) -> dict[str, str]:
    result = DEFAULT_STYLE_TEMPLATES.copy()
    if isinstance(value, Mapping):
        for name in STYLE_PRESETS:
            if name in value:
                result[name] = str(value[name] or "")
    return result


def _add_language_guidance(template: str, language_guidance: object) -> str:
    guidance = (
        DEFAULT_LANGUAGE_GUIDANCE
        if language_guidance is None
        else str(language_guidance).strip()
    )
    if not guidance:
        return template
    return f"{template.rstrip()}\n{guidance}" if template.strip() else guidance


def resolve_style(
    style: str | None,
    templates: Mapping[str, str] | None = None,
    *,
    empty_behavior: str = "none",
    language_guidance: object = None,
) -> str | None:
    """Resolve a preset while preserving unknown styles verbatim."""
    resolved_templates = style_templates(templates)
    if style is None or not str(style).strip():
        return (
            _add_language_guidance(resolved_templates["natural"], language_guidance)
            if empty_behavior == "natural"
            else None
        )
    value = str(style)
    return (
        _add_language_guidance(resolved_templates[value], language_guidance)
        if value in STYLE_PRESETS
        else value
    )


def normalize_style_selection(value: object) -> str:
    candidate = str(value or "").strip().lower()
    return candidate if candidate in STYLE_PRESETS else "natural"
