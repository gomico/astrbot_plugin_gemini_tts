from __future__ import annotations

import random


def should_attempt_auto_tts(
    enabled: bool,
    probability: float,
    *,
    readable_text: bool,
    already_processed: bool,
    draw: float | None = None,
) -> bool:
    if not enabled or not readable_text or already_processed:
        return False
    probability = min(1.0, max(0.0, float(probability)))
    if probability == 0:
        return False
    if probability == 1:
        return True
    return (random.random() if draw is None else draw) < probability
