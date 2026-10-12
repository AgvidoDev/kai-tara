"""Middleware: язык пользователя в каждом обработчике (аргумент lang)."""
from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from .i18n import detect

_cache: dict[int, str] = {}


def remember(tg_id: int, lang: str) -> None:
    _cache[tg_id] = lang


def forget(tg_id: int) -> None:
    _cache.pop(tg_id, None)


class LangMiddleware(BaseMiddleware):
    """Язык из базы (с кэшем); у новых пользователей — по языку приложения Telegram."""

    async def __call__(self, handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject, data: dict[str, Any]) -> Any:
        user: User | None = data.get("event_from_user")
        lang = "ru"
        if user:
            lang = _cache.get(user.id)
            if lang is None:
                repo = data.get("repo")
                stored = await repo.get_lang(user.id) if repo else None
                lang = stored or detect(user.language_code)
                if stored:
                    _cache[user.id] = stored
        data["lang"] = lang
        return await handler(event, data)
