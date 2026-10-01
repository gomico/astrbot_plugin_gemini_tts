from __future__ import annotations

import re

_COMMAND = re.compile(r"^/?GEMINITTS(?:\s|$)", re.IGNORECASE)


def parse_gemini_tts_command(message: str) -> tuple[str, str | None]:
    """Parse one command without changing transcript whitespace."""
    raw = str(message or "")
    match = _COMMAND.match(raw)
    payload = raw[match.end() :] if match else raw
    if "&&" not in payload:
        return payload, None
    text, style = payload.rsplit("&&", 1)
    return text, style.strip()
