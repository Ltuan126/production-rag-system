from __future__ import annotations

import asyncio
from dataclasses import dataclass


@dataclass
class _CacheEntry:
    value: object


class ResponseCache:
    def __init__(self) -> None:
        self._store: dict[str, _CacheEntry] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> object | None:
        async with self._lock:
            entry = self._store.get(key)
            return None if entry is None else entry.value

    async def set(self, key: str, value: object) -> None:
        async with self._lock:
            self._store[key] = _CacheEntry(value=value)