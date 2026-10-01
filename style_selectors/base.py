from __future__ import annotations

from typing import Protocol


class StyleSelector(Protocol):
    async def select(self, event: object, text: str) -> str:
        ...
