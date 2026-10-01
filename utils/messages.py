from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def _kind(component: Any) -> str:
    value = getattr(component, "type", None)
    value = getattr(value, "value", value)
    return str(value or component.__class__.__name__).lower()


def is_plain(component: Any) -> bool:
    return _kind(component) in {"plain", "text"} or component.__class__.__name__ == "Plain"


def is_record(component: Any) -> bool:
    return _kind(component) == "record" or component.__class__.__name__ == "Record"


def has_record(chain: Iterable[Any]) -> bool:
    return any(is_record(component) for component in chain)


def plain_text(chain: Iterable[Any]) -> str | None:
    parts = [str(getattr(component, "text", "")) for component in chain if is_plain(component)]
    return "".join(parts) if parts else None


def replace_plain_components(chain: list[Any], record: Any) -> bool:
    indexes = [i for i, component in enumerate(chain) if is_plain(component)]
    if not indexes:
        return False
    first = indexes[0]
    chain[:] = [
        record if i == first else component
        for i, component in enumerate(chain)
        if i not in indexes or i == first
    ]
    return True
