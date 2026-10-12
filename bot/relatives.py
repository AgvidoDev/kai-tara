"""Близкие: профили родных и друзей. Хранятся имя и астропрофиль, дата/время/место рождения — нет."""
from __future__ import annotations

import asyncio
import re
from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from jyotish.compat import compat

from . import keyboards as kb
from .astro_service import compute_profile, daily_personal, describe_profile, render_compat, render_daily, settings_for
from .config import Config
from .db import Repo
from .handlers import rich
from .i18n import t
from .payments import is_premium, send_paywall
from .places import from_key, resolve_text

router = Router()
LIMIT = 10
NAME_MAX = 32


class Rel(StatesGroup):
    name = State()
    date = State()
    time = State()
    place = State()


def _btn(text: str, data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=data)


async def _gate(m: Message, tg_id: int, repo: Repo, cfg: Config, lang: str):
    u = await repo.get_user(tg_id)
    if not u or not u["has_birth"]:
        await m.answer(t(lang, "need_birth"))
        return None
    if not is_premium(u, cfg):
        await send_paywall(m, cfg, t(lang, "feat_relatives"), lang=lang)
        return None
    return u


async def _show_list(m: Message, tg_id: int, repo: Repo, lang: str) -> None:
    items = await repo.relatives(tg_id)
    rows = [[_btn(f"👤 {name}", f"rel:card:{rid}")] for rid, name in items]
    if len(items) < LIMIT:
        rows.append([_btn(t(lang, "kb_rel_add"), "rel:add")])
    text = t(lang, "rel_list") if items else t(lang, "rel_empty")
    await m.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


@router.message(Command("family"))
@router.message(F.text.in_(kb.BTN_FAMILY))
async def family(m: Message, repo: Repo, cfg: Config, lang: str):
    if await _gate(m, m.from_user.id, repo, cfg, lang):
        await _show_list(m, m.from_user.id, repo, lang)


@router.callback_query(F.data == "rel:list")
async def family_cb(c: CallbackQuery, repo: Repo, cfg: Config, lang: str):
    await c.answer()
    if await _gate(c.message, c.from_user.id, repo, cfg, lang):
        await _show_list(c.message, c.from_user.id, repo, lang)


# ------------------------------------------------------------------ добавление
@router.callback_query(F.data == "rel:add")
async def add_start(c: CallbackQuery, repo: Repo, cfg: Config, state: FSMContext, lang: str):
    await c.answer()
    if not await _gate(c.message, c.from_user.id, repo, cfg, lang):
        return
    if len(await repo.relatives(c.from_user.id)) >= LIMIT:
        return await c.message.answer(t(lang, "rel_limit", n=LIMIT))
    await state.set_state(Rel.name)
    await c.message.answer(t(lang, "rel_ask_name"))


@router.message(Rel.name)
async def add_name(m: Message, state: FSMContext, lang: str):
    name = " ".join((m.text or "").split())
    if not name or len(name) > NAME_MAX or name.startswith("/"):
        return await m.answer(t(lang, "rel_bad_name", n=NAME_MAX))
    await state.update_data(r_name=name)
    await state.set_state(Rel.date)
    await m.answer(t(lang, "rel_ask_date", name=escape(name)))


@router.message(Rel.date)
async def add_date(m: Message, state: FSMContext, lang: str):
    try:
        d = datetime.strptime((m.text or "").strip(), "%d.%m.%Y")
        if not 1900 <= d.year <= datetime.now().year:
            raise ValueError
    except ValueError:
        return await m.answer(t(lang, "bad_p_date"))
    await state.update_data(r_date=d.strftime("%Y-%m-%d"))
    await state.set_state(Rel.time)
    await m.answer(t(lang, "rel_ask_time"),
                   reply_markup=InlineKeyboardMarkup(inline_keyboard=[[_btn(t(lang, "kb_time_unknown"),
                                                                            "rtime:unknown")]]))


@router.message(Rel.time)
async def add_time(m: Message, state: FSMContext, lang: str):
    tm = (m.text or "").strip()
    if not re.fullmatch(r"([01]?\d|2[0-3]):[0-5]\d", tm):
        return await m.answer(t(lang, "bad_time"))
    await state.update_data(r_time=tm, r_known=True)
    await _ask_place(m, state, lang)


@router.callback_query(Rel.time, F.data == "rtime:unknown")
async def add_no_time(c: CallbackQuery, state: FSMContext, lang: str):
    await state.update_data(r_time="12:00", r_known=False)
    await c.message.edit_reply_markup()
    await _ask_place(c.message, state, lang)
    await c.answer()


async def _ask_place(m: Message, state: FSMContext, lang: str) -> None:
    await state.set_state(Rel.place)
    await m.answer(t(lang, "rel_ask_place"), reply_markup=kb.cities("rplace", lang))
    await m.answer(t(lang, "place_hint"), reply_markup=kb.place_reply(lang))


@router.callback_query(Rel.place, F.data.startswith("rplace:"))
async def add_city(c: CallbackQuery, repo: Repo, state: FSMContext, lang: str):
    place = from_key(c.data.split(":", 1)[1], lang)
    if not place:
        return await c.answer()
    await c.message.edit_reply_markup()
    await _finish(c.message, c.from_user.id, repo, state, place[0], place[1], place[2], lang)
    await c.answer()


@router.message(Rel.place, F.location)
async def add_geo(m: Message, repo: Repo, state: FSMContext, lang: str):
    from .places import tz_at
    lat, lon = m.location.latitude, m.location.longitude
    await _finish(m, m.from_user.id, repo, state, lat, lon, tz_at(lat, lon), lang)


@router.message(Rel.place)
async def add_text(m: Message, repo: Repo, state: FSMContext, lang: str):
    place = await resolve_text(m, lang, "rplace")
    if place:
        await _finish(m, m.from_user.id, repo, state, place[0], place[1], place[2], lang)


async def _finish(m: Message, tg_id: int, repo: Repo, state: FSMContext, lat: float, lon: float, tz: str,
                  lang: str) -> None:
    data = await state.get_data()
    await state.clear()                       # дата, время и место рождения стираются здесь
    birth = datetime.strptime(f"{data['r_date']} {data['r_time']}", "%Y-%m-%d %H:%M")
    prof = await asyncio.to_thread(compute_profile, birth, lat, lon, tz, data["r_known"])
    rid = await repo.add_relative(tg_id, data["r_name"], prof, LIMIT)
    if rid is None:
        await m.answer(t(lang, "rel_limit", n=LIMIT), reply_markup=kb.main_menu(lang))
        return
    await m.answer(t(lang, "rel_saved", name=escape(data["r_name"])), reply_markup=kb.main_menu(lang))
    await _card(m, tg_id, rid, repo, lang)


# ------------------------------------------------------------------ карточка
async def _card(m: Message, tg_id: int, rid: int, repo: Repo, lang: str) -> None:
    from .period_view import dasha_text
    rel = await repo.get_relative(tg_id, rid)
    if not rel:
        await m.answer(t(lang, "rel_not_found"))
        return
    name, prof = rel
    u = await repo.get_user(tg_id)
    lines = [f"👤 <b>{escape(name)}</b>", "", describe_profile(prof, lang)]
    if prof.dashas:
        md, ad = prof.current_dasha(datetime.now(ZoneInfo(u["tz"])))
        if md:
            lines += ["", dasha_text(md, ad, lang)]
    if not prof.time_known:
        lines += ["", t(lang, "rel_no_time")]
    rows = [[_btn(t(lang, "kb_rel_day"), f"rel:day:{rid}"), _btn(t(lang, "kb_rel_compat"), f"rel:cmp:{rid}")],
            [_btn(t(lang, "kb_rel_del"), f"rel:del:{rid}"), _btn(t(lang, "kb_rel_back"), "rel:list")]]
    text, kbd = rich("\n".join(lines), lang)
    kbd.inline_keyboard[:0] = rows
    await m.answer(text, reply_markup=kbd)


def _rid(data: str) -> int | None:
    try:
        return int(data.rsplit(":", 1)[1])
    except (ValueError, IndexError):
        return None


@router.callback_query(F.data.startswith("rel:card:"))
async def card_cb(c: CallbackQuery, repo: Repo, cfg: Config, lang: str):
    await c.answer()
    rid = _rid(c.data)
    if rid is not None and await _gate(c.message, c.from_user.id, repo, cfg, lang):
        await _card(c.message, c.from_user.id, rid, repo, lang)


@router.callback_query(F.data.startswith("rel:day:"))
async def day_cb(c: CallbackQuery, repo: Repo, cfg: Config, lang: str):
    await c.answer()
    rid = _rid(c.data)
    u = await _gate(c.message, c.from_user.id, repo, cfg, lang)
    rel = await repo.get_relative(c.from_user.id, rid) if u and rid is not None else None
    if not u:
        return
    if not rel:
        return await c.message.answer(t(lang, "rel_not_found"))
    name, prof = rel
    s = settings_for(u["city_key"])
    d = datetime.now(ZoneInfo(u["tz"])).date()
    p = await asyncio.to_thread(daily_personal, d, s, prof.moon_rashi, prof.moon_nakshatra)
    text, kbd = rich(render_daily(p, True, lang, u["city_key"], who=name), lang)
    await c.message.answer(text, reply_markup=kbd)


@router.callback_query(F.data.startswith("rel:cmp:"))
async def compat_cb(c: CallbackQuery, repo: Repo, cfg: Config, lang: str):
    await c.answer()
    rid = _rid(c.data)
    if rid is None or not await _gate(c.message, c.from_user.id, repo, cfg, lang):
        return
    await c.message.answer(t(lang, "rel_compat_who"), reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
        _btn(t(lang, "kb_male"), f"relc:m:{rid}"), _btn(t(lang, "kb_female"), f"relc:f:{rid}")]]))


@router.callback_query(F.data.startswith("relc:"))
async def compat_go(c: CallbackQuery, repo: Repo, cfg: Config, lang: str):
    await c.answer()
    rid = _rid(c.data)
    if rid is None or not await _gate(c.message, c.from_user.id, repo, cfg, lang):
        return
    await c.message.edit_reply_markup()
    rel = await repo.get_relative(c.from_user.id, rid)
    me = await repo.load_profile(c.from_user.id)
    if not rel:
        return await c.message.answer(t(lang, "rel_not_found"))
    name, prof = rel
    if not me or me.moon is None or prof.moon is None:
        return await c.message.answer(t(lang, "rel_compat_need_moon"))
    you = t(lang, "you")
    if c.data.split(":")[1] == "m":
        a, b, an, bn = me.moon, prof.moon, you, name
    else:
        a, b, an, bn = prof.moon, me.moon, name, you
    text, kbd = rich(render_compat(compat(a, b), a, b, an, bn, lang), lang)
    await c.message.answer(text, reply_markup=kbd)


# ------------------------------------------------------------------ удаление
@router.callback_query(F.data.startswith("rel:del:"))
async def del_ask(c: CallbackQuery, lang: str):
    await c.answer()
    rid = _rid(c.data)
    if rid is None:
        return
    await c.message.answer(t(lang, "rel_del_confirm"), reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
        _btn(t(lang, "kb_del_yes"), f"rel:delok:{rid}"), _btn(t(lang, "kb_cancel"), "rel:list")]]))


@router.callback_query(F.data.startswith("rel:delok:"))
async def del_ok(c: CallbackQuery, repo: Repo, lang: str):
    await c.answer()
    rid = _rid(c.data)
    await c.message.edit_reply_markup()
    ok = rid is not None and await repo.delete_relative(c.from_user.id, rid)
    await c.message.answer(t(lang, "rel_deleted" if ok else "rel_not_found"))
    await _show_list(c.message, c.from_user.id, repo, lang)
