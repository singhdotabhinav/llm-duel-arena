from __future__ import annotations

import time
from typing import Dict


class SimpleTokenTracker:
    def __init__(self) -> None:
        self._usage: Dict[str, int] = {}

    def add(self, key: str, tokens: int) -> int:
        self._usage[key] = self._usage.get(key, 0) + tokens
        return self._usage[key]

    def get(self, key: str) -> int:
        return self._usage.get(key, 0)


token_tracker = SimpleTokenTracker()












