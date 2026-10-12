"""Вход в Mini App из чата: команда /app с кнопкой WebApp."""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from .config import Config
from .i18n import t

router = Router()


def app_button(cfg: Config, lang: str) -> InlineKeyboardButton | None:
    if not cfg.webapp_url:
        return None
    return InlineKeyboardButton(text=t(lang, "kb_open_app"), web_app=WebAppInfo(url=cfg.webapp_url + "/"))


@router.message(Command("app"))
async def app_cmd(m: Message, cfg: Config, lang: str):
    btn = app_button(cfg, lang)
    if not btn:
        await m.answer(t(lang, "app_off"))
        return
    await m.answer(t(lang, "app_intro"), reply_markup=InlineKeyboardMarkup(inline_keyboard=[[btn]]))
