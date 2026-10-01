from __future__ import annotations

from collections.abc import Mapping

PREBUILT_VOICES = (
    "Zephyr", "Puck", "Charon", "Kore", "Fenrir", "Leda", "Orus", "Aoede",
    "Callirrhoe", "Autonoe", "Enceladus", "Iapetus", "Umbriel", "Algieba",
    "Despina", "Erinome", "Algenib", "Rasalgethi", "Laomedeia", "Achernar",
    "Alnilam", "Schedar", "Gacrux", "Pulcherrima", "Achird", "Zubenelgenubi",
    "Vindemiatrix", "Sadachbia", "Sadaltager", "Sulafat",
)


def resolve_voice(
    prebuilt_voice: str = "Kore",
    voice_id_override: str = "",
    custom_voice_alias: str = "",
    custom_voice_aliases: Mapping[str, object] | None = None,
) -> str:
    """Resolve voice IDs in the documented precedence order."""
    override = str(voice_id_override or "").strip()
    if override:
        return override
    alias = str(custom_voice_alias or "").strip()
    aliases = custom_voice_aliases or {}
    if alias and alias in aliases:
        voice_id = str(aliases[alias] or "").strip()
        if voice_id:
            return voice_id
    return str(prebuilt_voice or "Kore").strip() or "Kore"
