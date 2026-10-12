"""Разделы: прогноз на сегодня, календарь, совместимость, словарь терминов."""
from __future__ import annotations

import asyncio
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from timezonefinder import TimezoneFinder

from jyotish.compat import compat
from jyotish.core import city_name
from jyotish.glossary import categories, find_terms, terms
from jyotish.profile import MoonPoint

from . import keyboards as kb
from .astro_service import (calendar_for, daily_personal, moon_lon, render_calendar, render_compat,
                            render_daily, settings_for)
from .config import Config
from .db import Repo
from .glossary import card, categories_keyboard, category_keyboard, linkify, terms_keyboard
from .handlers import rich
from .i18n import t
from .payments import is_premium, send_paywall
from .places import from_key, resolve_text

router = Router()
_tf = TimezoneFinder()


async def _user_with_birth(m: Message, repo: Repo, lang: str):
    u = await repo.get_user(m.from_user.id)
    if not u or not u["has_birth"]:
        await m.answer(t(lang, "need_birth"))
        return None
    return u


# ------------------------------------------------------------------ сегодня
@router.message(Command("today"))
@router.message(F.text.in_(kb.BTN_TODAY))
async def today(m: Message, repo: Repo, cfg: Config, lang: str):
    u = await _user_with_birth(m, repo, lang)
    if not u:
        return
    s = settings_for(u["city_key"])
    d = datetime.now(ZoneInfo(u["tz"])).date()
    p = await asyncio.to_thread(daily_personal, d, s, u["moon_rashi"], u["moon_nakshatra"])
    full = is_premium(u, cfg)
    text, kbd = rich(render_daily(p, full, lang, u["city_key"]), lang)
    if full:
        from .period_view import period_buttons
        from .why import why_button
        kbd.inline_keyboard[0].append(why_button("day", lang))
        kbd.inline_keyboard.append(period_buttons(lang))
    await m.answer(text, reply_markup=kbd)


# ------------------------------------------------------------------ календарь
@router.message(Command("calendar"))
@router.message(F.text.in_(kb.BTN_CALENDAR))
async def calendar(m: Message, repo: Repo, cfg: Config, lang: str):
    u = await _user_with_birth(m, repo, lang)
    if not u:
        return
    if not is_premium(u, cfg):
        return await send_paywall(m, cfg, t(lang, "feat_calendar"), lang=lang)
    s = settings_for(u["city_key"])
    d = datetime.now(ZoneInfo(u["tz"])).date()
    await m.answer(t(lang, "counting"))
    cal = await asyncio.to_thread(calendar_for, d, s, u["moon_rashi"], u["moon_nakshatra"])
    text, kbd = rich(render_calendar(cal, city_name(u["city_key"], lang), lang), lang)
    from .ics import ics_button
    kbd.inline_keyboard.append([ics_button(lang)])
    await m.answer(text, reply_markup=kbd)


# ------------------------------------------------------------------ совместимость
class Partner(StatesGroup):
    gender = State()
    date = State()
    time = State()
    place = State()


@router.message(Command("compat"))
@router.message(F.text.in_(kb.BTN_COMPAT))
async def compat_start(m: Message, repo: Repo, cfg: Config, state: FSMContext, lang: str):
    u = await _user_with_birth(m, repo, lang)
    if not u:
        return
    if not is_premium(u, cfg) and u["compat_credits"] <= 0:
        return await send_paywall(m, cfg, t(lang, "feat_compat"), with_compat=True, lang=lang)
    await state.set_state(Partner.gender)
    await m.answer(t(lang, "compat_intro"), reply_markup=kb.gender(lang))


@router.callback_query(Partner.gender, F.data.startswith("cg:"))
async def compat_gender(c: CallbackQuery, state: FSMContext, lang: str):
    await state.update_data(user_male=c.data == "cg:m")
    await state.set_state(Partner.date)
    await c.message.edit_reply_markup()
    await c.message.answer(t(lang, "ask_p_date"))
    await c.answer()


@router.message(Partner.date)
async def compat_date(m: Message, state: FSMContext, lang: str):
    try:
        d = datetime.strptime((m.text or "").strip(), "%d.%m.%Y")
        if not 1900 <= d.year <= datetime.now().year:
            raise ValueError
    except ValueError:
        return await m.answer(t(lang, "bad_p_date"))
    await state.update_data(p_date=d.strftime("%Y-%m-%d"))
    await state.set_state(Partner.time)
    await m.answer(t(lang, "ask_p_time"), reply_markup=kb.partner_time_unknown(lang))


@router.message(Partner.time)
async def compat_time(m: Message, state: FSMContext, lang: str):
    tm = (m.text or "").strip()
    if not re.fullmatch(r"([01]?\d|2[0-3]):[0-5]\d", tm):
        return await m.answer(t(lang, "bad_time"))
    await state.update_data(p_time=tm, p_time_known=True)
    await _ask_partner_place(m, state, lang)


@router.callback_query(Partner.time, F.data == "ptime:unknown")
async def compat_no_time(c: CallbackQuery, state: FSMContext, lang: str):
    await state.update_data(p_time="12:00", p_time_known=False)
    await c.message.edit_reply_markup()
    await _ask_partner_place(c.message, state, lang)
    await c.answer()


async def _ask_partner_place(m: Message, state: FSMContext, lang: str):
    await state.set_state(Partner.place)
    await m.answer(t(lang, "ask_p_place"), reply_markup=kb.cities("pplace", lang))
    await m.answer(t(lang, "place_hint"), reply_markup=kb.place_reply(lang))


@router.callback_query(Partner.place, F.data.startswith("pplace:"))
async def compat_city(c: CallbackQuery, repo: Repo, cfg: Config, state: FSMContext, lang: str):
    place = from_key(c.data.split(":", 1)[1], lang)
    if not place:
        return await c.answer()
    await c.message.edit_reply_markup()
    await _compat_finish(c.message, c.from_user.id, repo, cfg, state, place[2], lang)
    await c.answer()


@router.message(Partner.place, F.location)
async def compat_geo(m: Message, repo: Repo, cfg: Config, state: FSMContext, lang: str):
    from .places import tz_at
    await _compat_finish(m, m.from_user.id, repo, cfg, state, tz_at(m.location.latitude, m.location.longitude), lang)


@router.message(Partner.place)
async def compat_text(m: Message, repo: Repo, cfg: Config, state: FSMContext, lang: str):
    place = await resolve_text(m, lang, "pplace")
    if place:
        await _compat_finish(m, m.from_user.id, repo, cfg, state, place[2], lang)


async def _compat_finish(m: Message, tg_id: int, repo: Repo, cfg: Config, state: FSMContext, p_tz: str, lang: str):
    data = await state.get_data()
    await state.clear()
    u = await repo.get_user(tg_id)
    if not is_premium(u, cfg) and not await repo.use_compat_credit(tg_id):
        return await send_paywall(m, cfg, t(lang, "feat_compat"), with_compat=True, lang=lang)
    prof = await repo.load_profile(tg_id)
    me_moon = prof.moon if prof else None
    if me_moon is None:
        if not is_premium(u, cfg):
            await repo.add_compat_credit(tg_id)          # кредит не сгорает
        return await m.answer(t(lang, "compat_need_moon"))
    p_dt = datetime.strptime(f"{data['p_date']} {data['p_time']}", "%Y-%m-%d %H:%M")
    p_lon, p_ok = await asyncio.to_thread(moon_lon, p_dt, p_tz, data["p_time_known"])
    my_moon, p_moon = me_moon, MoonPoint.from_lon(p_lon)
    you, partner = t(lang, "you"), t(lang, "partner")
    if data["user_male"]:
        a, b, an, bn = my_moon, p_moon, you, partner
    else:
        a, b, an, bn = p_moon, my_moon, partner, you
    text = render_compat(compat(a, b), a, b, an, bn, lang)
    if not p_ok:
        text += t(lang, "warn_line", items=t(lang, "warn_p"))
    text, kbd = rich(text, lang)
    await m.answer(text, reply_markup=kbd)
    await m.answer(t(lang, "compat_again", btn=t(lang, "btn_compat")), reply_markup=kb.main_menu(lang))


# ------------------------------------------------------------------ словарь
@router.message(Command("glossary"))
async def glossary(m: Message, lang: str):
    await m.answer(t(lang, "gloss_intro"), reply_markup=categories_keyboard(lang))


@router.callback_query(F.data == "glcat")
async def glossary_cats(c: CallbackQuery, lang: str):
    await c.message.answer(t(lang, "gloss_choose"), reply_markup=categories_keyboard(lang))
    await c.answer()


@router.callback_query(F.data.startswith("glc:"))
async def glossary_cat(c: CallbackQuery, lang: str):
    cat = c.data[4:]
    cats = categories(lang)
    if cat not in cats:
        return await c.answer()
    await c.message.edit_text(f"📚 <b>{cats[cat]}</b>", reply_markup=category_keyboard(cat, lang))
    await c.answer()


@router.callback_query(F.data.startswith("gl:"))
async def glossary_term(c: CallbackQuery, lang: str):
    key = c.data[3:]
    if key not in terms(lang):
        return await c.answer(t(lang, "term_not_found"))
    text, kbd = card(key, lang=lang)
    await c.message.answer(text, reply_markup=kbd)
    await c.answer()


@router.callback_query(F.data.startswith("glm:"))
async def glossary_more(c: CallbackQuery, lang: str):
    key = c.data[4:]
    if key not in terms(lang):
        return await c.answer()
    text, kbd = card(key, full=True, lang=lang)
    await c.message.edit_text(text, reply_markup=kbd)
    await c.answer()


@router.callback_query(F.data == "gll")
async def glossary_in_message(c: CallbackQuery, lang: str):
    keys = find_terms(c.message.text or "", lang)
    if not keys:
        return await c.answer(t(lang, "no_terms"), show_alert=True)
    await c.message.answer(t(lang, "terms_in_msg"), reply_markup=terms_keyboard(keys, lang))
    await c.answer()


# ------------------------------------------------------------------ натальная карта
class ChartInput(StatesGroup):
    date = State()
    time = State()
    place = State()


@router.message(Command("chart"))
async def chart_start(m: Message, state: FSMContext, lang: str):
    await state.set_state(ChartInput.date)
    await m.answer(t(lang, "chart_intro"), reply_markup=kb.remove)


@router.callback_query(F.data == "chart:new")
async def chart_start_cb(c: CallbackQuery, state: FSMContext, lang: str):
    await state.set_state(ChartInput.date)
    await c.message.answer(t(lang, "chart_intro"))
    await c.answer()


@router.message(ChartInput.date)
async def chart_date(m: Message, state: FSMContext, lang: str):
    try:
        d = datetime.strptime((m.text or "").strip(), "%d.%m.%Y")
        if not 1900 <= d.year <= datetime.now().year:
            raise ValueError
    except ValueError:
        return await m.answer(t(lang, "bad_date"))
    await state.update_data(c_date=d.strftime("%Y-%m-%d"))
    await state.set_state(ChartInput.time)
    await m.answer(t(lang, "ask_time"), reply_markup=_chart_time_kb(lang))


def _chart_time_kb(lang: str):
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(lang, "kb_time_unknown"),
                                                                       callback_data="ctime:unknown")]])


@router.message(ChartInput.time)
async def chart_time(m: Message, state: FSMContext, lang: str):
    tm = (m.text or "").strip()
    if not re.fullmatch(r"([01]?\d|2[0-3]):[0-5]\d", tm):
        return await m.answer(t(lang, "bad_time"))
    await state.update_data(c_time=tm, c_known=True)
    await _chart_ask_place(m, state, lang)


@router.callback_query(ChartInput.time, F.data == "ctime:unknown")
async def chart_no_time(c: CallbackQuery, state: FSMContext, lang: str):
    await state.update_data(c_time="12:00", c_known=False)
    await c.message.edit_reply_markup()
    await _chart_ask_place(c.message, state, lang)
    await c.answer()


async def _chart_ask_place(m: Message, state: FSMContext, lang: str):
    await state.set_state(ChartInput.place)
    await m.answer(t(lang, "ask_place"), reply_markup=kb.cities("cplace", lang))
    await m.answer(t(lang, "place_hint"), reply_markup=kb.place_reply(lang))


@router.callback_query(ChartInput.place, F.data.startswith("cplace:"))
async def chart_city(c: CallbackQuery, state: FSMContext, lang: str, repo: Repo, cfg: Config):
    place = from_key(c.data.split(":", 1)[1], lang)
    if not place:
        return await c.answer()
    await c.message.edit_reply_markup()
    lat, lon, tz, name = place[:4]
    await _chart_finish(c.message, state, lat, lon, tz, name, lang, repo, cfg)
    await c.answer()


@router.message(ChartInput.place, F.location)
async def chart_geo(m: Message, state: FSMContext, lang: str, repo: Repo, cfg: Config):
    lat, lon = m.location.latitude, m.location.longitude
    tz = _tf.timezone_at(lat=lat, lng=lon) or "UTC"
    await _chart_finish(m, state, lat, lon, tz, f"{lat:.2f}, {lon:.2f}", lang, repo, cfg)


@router.message(ChartInput.place)
async def chart_text(m: Message, state: FSMContext, lang: str, repo: Repo, cfg: Config):
    place = await resolve_text(m, lang, "cplace")
    if place:
        lat, lon, tz, name = place[:4]
        await _chart_finish(m, state, lat, lon, tz, name, lang, repo, cfg)


async def _chart_finish(m: Message, state: FSMContext, lat: float, lon: float, tz: str, place: str, lang: str,
                        repo: Repo, cfg: Config):
    from aiogram.types import BufferedInputFile

    from jyotish.core import Location, Settings
    from jyotish.natal import build_chart

    from .chart_view import render_png, render_text
    from .report_flow import keep_chart, report_keyboard
    from .report_pdf import summary
    from jyotish.report import analyze

    data = await state.get_data()
    await state.clear()
    loc = Location(place, lat, lon, tz)
    birth = datetime.strptime(f"{data['c_date']} {data['c_time']}", "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo(tz))
    known = data["c_known"]
    ch = await asyncio.to_thread(build_chart, birth, loc, Settings(location=loc))
    png = await asyncio.to_thread(render_png, ch, lang, known, place)
    await m.answer_photo(BufferedInputFile(png, "chart.png"), caption=t(lang, "chart_caption"),
                         reply_markup=kb.main_menu(lang))
    text, kbd = rich(render_text(ch, datetime.now(ZoneInfo(tz)), lang, known), lang)
    await m.answer(text, reply_markup=kbd)
    # данные карты — только в памяти бота (FSM), не дольше 30 минут: для PDF-разбора
    await keep_chart(state, {"date": data["c_date"], "time": data["c_time"], "known": known,
                             "lat": lat, "lon": lon, "tz": tz, "place": place})
    r = await asyncio.to_thread(analyze, ch, datetime.now(ZoneInfo(tz)), known)
    u = await repo.get_user(m.chat.id)
    await m.answer(linkify(summary(r, lang), lang=lang), reply_markup=report_keyboard(u, cfg, lang))
    await m.answer(t(lang, "chart_again"))
