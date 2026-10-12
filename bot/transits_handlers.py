"""Большие транзиты в боте: /transits, прогноз по знаку, личная версия, пуши (анонс и день события)."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from jyotish.transits import BigTransit, big_transits

from .config import Config
from .db import Repo
from .glossary import linkify, terms_button
from .i18n import t
from .payments import is_premium, send_paywall
from .transits_view import render_for_sign, render_personal, short_title, sign_for, teaser

log = logging.getLogger("transits")
router = Router()

def transits_button(lang: str = "ru") -> InlineKeyboardButton:
    return InlineKeyboardButton(text=t(lang, "kb_transits"), callback_data="tr:list")


TRANSITS_BUTTON = transits_button("ru")
PUSH_HOUR = 10                     # не раньше 10:00 по времени пользователя

_cache: dict[str, list[BigTransit]] = {}


def current(now: datetime | None = None) -> list[BigTransit]:
    """Транзиты, начавшиеся за последние 120 дней или в ближайшие 90 (кэш на сутки)."""
    now = now or datetime.now(timezone.utc)
    key = f"{now:%Y-%m-%d}"
    if key not in _cache:
        _cache.clear()
        _cache[key] = big_transits(now)
    return _cache[key]


def _find(key: str) -> BigTransit | None:
    return next((t for t in current() if t.key == key), None)


def list_keyboard(ts: list[BigTransit], lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=short_title(x, lang),
                                                                       callback_data=f"tr:{x.key}")] for x in ts])


def transit_keyboard(tr: BigTransit, lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "kb_transit_personal"), callback_data=f"trp:{tr.key}")],
        [terms_button(lang)],
    ])


async def _general_text(u, tr: BigTransit, lang: str = "ru") -> str | None:
    sign, note = sign_for(u["sign_mode"], u, tr.start.year, lang)
    if sign is None:                 # режим «по Луне» без точной Луны — берём сидерическое Солнце
        sign, note = u["sun_sid_rashi"], ""
    return linkify(render_for_sign(tr, sign, note, lang), lang=lang)


@router.message(Command("transits"))
async def transits_cmd(m: Message, repo: Repo, lang: str):
    await _show_list(m, repo, m.from_user.id, lang)


@router.callback_query(F.data == "tr:list")
async def transits_list(c: CallbackQuery, repo: Repo, lang: str):
    await _show_list(c.message, repo, c.from_user.id, lang)
    await c.answer()


async def _show_list(m: Message, repo: Repo, tg_id: int, lang: str):
    u = await repo.get_user(tg_id)
    if not u or not u["has_birth"]:
        return await m.answer(t(lang, "need_birth"))
    ts = await asyncio.to_thread(current)
    if not ts:
        return await m.answer(t(lang, "no_transits"))
    await m.answer(t(lang, "transits_intro"), reply_markup=list_keyboard(ts, lang))


@router.callback_query(F.data.startswith("tr:") & (F.data != "tr:list"))
async def transit_general(c: CallbackQuery, repo: Repo, lang: str):
    tr = await asyncio.to_thread(lambda: _find(c.data[3:]))
    u = await repo.get_user(c.from_user.id)
    if not tr or not u or not u["has_birth"]:
        return await c.answer(t(lang, "transit_missing"), show_alert=True)
    await c.message.answer(await _general_text(u, tr, lang), reply_markup=transit_keyboard(tr, lang))
    await c.answer()


@router.callback_query(F.data.startswith("trp:"))
async def transit_personal(c: CallbackQuery, repo: Repo, cfg: Config, lang: str):
    u = await repo.get_user(c.from_user.id)
    if not is_premium(u, cfg):
        await send_paywall(c.message, cfg, t(lang, "feat_transit_personal"), lang=lang)
        return await c.answer()
    tr = await asyncio.to_thread(lambda: _find(c.data[4:]))
    prof = await repo.load_profile(c.from_user.id)
    if not tr or not prof:
        return await c.answer(t(lang, "no_data_short"), show_alert=True)
    await c.message.answer(linkify(render_personal(tr, prof, lang), lang=lang),
                           reply_markup=InlineKeyboardMarkup(inline_keyboard=[[terms_button(lang)]]))
    await c.answer()


# ------------------------------------------------------------------ пуши
def push_stage(t: BigTransit, today) -> str | None:
    """teaser — за 1–7 дней до события; day — в день события и ещё 2 дня (если пропустили)."""
    start = t.first_date.date()
    if timedelta(days=1) <= start - today <= timedelta(days=7):
        return "teaser"
    if timedelta(0) <= today - start <= timedelta(days=2):
        return "day"
    return None


async def send_transit_pushes(bot: Bot, repo: Repo) -> int:
    from .broadcast import safe_send_raw
    ts = await asyncio.to_thread(current)
    if not ts:
        return 0
    sent = 0
    for u in await repo.transit_push_candidates():
        now = datetime.now(ZoneInfo(u["tz"]))
        if now.hour < PUSH_HOUR:
            continue
        lang = u["lang"] or "ru"
        for tr in ts:
            stage = push_stage(tr, now.date())
            if not stage or not await repo.mark_transit_push(u["id"], tr.key, stage):
                continue
            try:
                if stage == "teaser":
                    days = (tr.first_date.date() - now.date()).days
                    kbd = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
                        text=t(lang, "kb_what_for_me"), callback_data=f"tr:{tr.key}")]])
                    sent += await safe_send_raw(bot, u["tg_id"], teaser(tr, days, lang), kbd)
                else:
                    sent += await safe_send_raw(bot, u["tg_id"], await _general_text(u, tr, lang),
                                                transit_keyboard(tr, lang))
            except Exception:
                log.exception("пуш транзита %s для %s", tr.key, u["tg_id"])
            await asyncio.sleep(0.05)
    return sent
