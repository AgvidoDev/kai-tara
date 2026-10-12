"""Хранилище состояний диалогов (FSM) с автоочисткой.

В состояниях временно лежат даты, время и место рождения (регистрация, совместимость, карта).
Всё, что не обновлялось дольше TTL, стирается фоновой задачей — даже если человек бросил ввод.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Mapping

from aiogram.fsm.state import State
from aiogram.fsm.storage.base import StateType, StorageKey
from aiogram.fsm.storage.memory import MemoryStorage

log = logging.getLogger("storage")
TTL = 30 * 60


class TTLMemoryStorage(MemoryStorage):
    def __init__(self, ttl: float = TTL) -> None:
        super().__init__()
        self.ttl = ttl
        self.touched: dict[StorageKey, float] = {}

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        await super().set_state(key, state)
        self._touch(key, state.state if isinstance(state, State) else state)

    async def set_data(self, key: StorageKey, data: Mapping[str, Any]) -> None:
        await super().set_data(key, data)
        self._touch(key, data)

    def _touch(self, key: StorageKey, value: Any) -> None:
        if value:
            self.touched[key] = time.time()

    def sweep(self, now: float | None = None) -> int:
        """Стирает состояния и данные, не обновлявшиеся дольше TTL. Возвращает число очищенных."""
        now = now or time.time()
        stale = [k for k, ts in self.touched.items() if now - ts > self.ttl]
        for k in stale:
            self.storage.pop(k, None)
            self.touched.pop(k, None)
        # записи без данных и состояния не храним
        for k in [k for k, rec in self.storage.items() if not rec.state and not rec.data]:
            self.storage.pop(k, None)
            self.touched.pop(k, None)
        return len(stale)

    async def sweeper(self, every: float = 60) -> None:
        while True:
            await asyncio.sleep(every)
            try:
                n = self.sweep()
                if n:
                    log.info("очищено устаревших состояний: %d", n)
            except Exception:
                log.exception("ошибка очистки состояний")
