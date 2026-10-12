from __future__ import annotations

import asyncio
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from timezonefinder import TimezoneFinder

from jyotish.core import CITIES, DEFAULT_CITY, city_name
from jyotish.glossary import terms
from jyotish.texts import SIGN, fmt_date

from . import keyboards as kb
from .astro_service import (MODE_NAMES, compute_profile, current_new_moon, describe_profile,
                            lunation_facts, personal_text, render_sign, settings_for)
from .config import Config
from .db import Repo
from .glossary import card, linkify, terms_button
from .i18n import t
from .lang import forget, remember
from .payments import is_premium, send_paywall
from .places import from_key, resolve_text

router = Router()
_tf = TimezoneFinder()


class Birth(StatesGroup):
    date = State()
    time = State()
    place = State()


class CityInput(StatesGroup):
    name = State()


def rich(html: str, lang: str = "ru") -> tuple[str, InlineKeyboardMarkup]:
    """Текст прогноза со ссылками на термины + кнопка списка терминов."""
    return linkify(html, lang=lang), InlineKeyboardMarkup(inline_keyboard=[[terms_button(lang)]])


def menu_buttons(lang: str) -> dict:
    return {"b1": t(lang, "btn_today"), "b2": t(lang, "btn_calendar"), "b3": t(lang, "btn_personal"),
            "b4": t(lang, "btn_compat")}


# ------------------------------------------------------------------ старт
@router.message(CommandStart(deep_link=True, magic=F.args.startswith("g_")))
async def start_glossary(m: Message, command: CommandObject, lang: str):
    key = command.args[2:]
    if key not in terms(lang):
        return await m.answer(t(lang, "term_missing"))
    text, kbd = card(key, lang=lang)
    await m.answer(text, reply_markup=kbd)


@router.message(CommandStart())
async def start(m: Message, repo: Repo, state: FSMContext, command: CommandObject, lang: str):
    await state.clear()
    await repo.ensure_user(m.from_user.id)
    if await repo.get_lang(m.from_user.id) is None:      # новичок: язык из Telegram, город по языку
        await repo.set_lang(m.from_user.id, lang)
        remember(m.from_user.id, lang)
        city = DEFAULT_CITY.get(lang, "moscow")
        await repo.set_city(m.from_user.id, city, CITIES[city].tz)
    if command.args and command.args.startswith("ref_") and command.args[4:].isdigit():
        await repo.set_referrer(m.from_user.id, int(command.args[4:]))
    u = await repo.get_user(m.from_user.id)
    if u["consent_pd_at"] is None:
        await m.answer(t(lang, "consent"), reply_markup=kb.consent(lang))
    elif not u["has_birth"]:
        await ask_date(m, state, lang)
    else:
        await m.answer(t(lang, "welcome_back"), reply_markup=kb.main_menu(lang))


@router.callback_query(F.data == "consent:yes")
async def consent(c: CallbackQuery, repo: Repo, state: FSMContext, lang: str):
    await repo.set_consent(c.from_user.id)
    await c.message.edit_reply_markup()
    await ask_date(c.message, state, lang)
    await c.answer()


@router.callback_query(F.data == "privacy")
async def privacy_cb(c: CallbackQuery, lang: str):
    await c.message.answer(t(lang, "privacy"))
    await c.answer()


@router.message(Command("privacy"))
async def privacy(m: Message, lang: str):
    await m.answer(t(lang, "privacy"))


async def ask_date(m: Message, state: FSMContext, lang: str):
    await state.set_state(Birth.date)
    await m.answer(t(lang, "ask_date"), reply_markup=kb.remove)


@router.message(Birth.date)
async def got_date(m: Message, state: FSMContext, lang: str):
    try:
        d = datetime.strptime((m.text or "").strip(), "%d.%m.%Y")
        if not 1900 <= d.year <= datetime.now().year:
            raise ValueError
    except ValueError:
        return await m.answer(t(lang, "bad_date"))
    await state.update_data(date=d.strftime("%Y-%m-%d"))
    await state.set_state(Birth.time)
    await m.answer(t(lang, "ask_time"), reply_markup=kb.time_unknown(lang))


@router.message(Birth.time)
async def got_time(m: Message, state: FSMContext, lang: str):
    tm = (m.text or "").strip()
    if not re.fullmatch(r"([01]?\d|2[0-3]):[0-5]\d", tm):
        return await m.answer(t(lang, "bad_time"))
    await state.update_data(time=tm, time_known=True)
    await ask_place(m, state, lang)


@router.callback_query(Birth.time, F.data == "time:unknown")
async def no_time(c: CallbackQuery, state: FSMContext, lang: str):
    await state.update_data(time="12:00", time_known=False)
    await c.message.edit_reply_markup()
    await ask_place(c.message, state, lang)
    await c.answer()


async def ask_place(m: Message, state: FSMContext, lang: str):
    await state.set_state(Birth.place)
    await m.answer(t(lang, "ask_place"), reply_markup=kb.cities("bplace", lang))
    await m.answer(t(lang, "place_hint"), reply_markup=kb.place_reply(lang))


@router.callback_query(Birth.place, F.data.startswith("bplace:"))
async def place_city(c: CallbackQuery, repo: Repo, state: FSMContext, cfg: Config, bot: Bot, lang: str):
    place = from_key(c.data.split(":", 1)[1], lang)
    if not place:
        return await c.answer()
    await c.message.edit_reply_markup()
    lat, lon, tz = place[:3]
    await finish_birth(c.message, c.from_user.id, repo, state, lat, lon, tz, cfg, bot, lang)
    await c.answer()


@router.message(Birth.place, F.location)
async def place_geo(m: Message, repo: Repo, state: FSMContext, cfg: Config, bot: Bot, lang: str):
    lat, lon = m.location.latitude, m.location.longitude
    await finish_birth(m, m.from_user.id, repo, state, lat, lon, _tz(lat, lon), cfg, bot, lang)


@router.message(Birth.place)
async def place_text(m: Message, repo: Repo, state: FSMContext, cfg: Config, bot: Bot, lang: str):
    place = await resolve_text(m, lang, "bplace")
    if place:
        lat, lon, tz = place[:3]
        await finish_birth(m, m.from_user.id, repo, state, lat, lon, tz, cfg, bot, lang)


def _tz(lat: float, lon: float) -> str:
    return _tf.timezone_at(lat=lat, lng=lon) or "UTC"


async def finish_birth(m: Message, tg_id: int, repo: Repo, state: FSMContext,
                       lat: float, lon: float, tz: str, cfg: Config, bot: Bot, lang: str):
    data = await state.get_data()
    birth_dt = datetime.strptime(f"{data['date']} {data['time']}", "%Y-%m-%d %H:%M")
    prof = await asyncio.to_thread(compute_profile, birth_dt, lat, lon, tz, data["time_known"])
    await repo.save_profile(tg_id, prof)          # дату, время и место рождения не сохраняем
    await state.clear()
    await m.answer(t(lang, "done_profile", profile=describe_profile(prof, lang)), reply_markup=kb.main_menu(lang))
    await m.answer(t(lang, "ask_mode"), reply_markup=kb.modes(prof.moon_rashi is not None, lang))
    until = await repo.start_trial(tg_id, cfg.trial_days)
    if cfg.free_mode:
        await m.answer(t(lang, "free_welcome", **menu_buttons(lang)))
    elif cfg.promo_active:
        await m.answer(t(lang, "promo_welcome", until=fmt_date(cfg.free_until, lang), **menu_buttons(lang)))
    elif until:
        await m.answer(t(lang, "trial_welcome", days=cfg.trial_days, **menu_buttons(lang)))
    ref = await repo.claim_referral(tg_id)
    if ref and await repo.extend_premium(ref, cfg.ref_bonus_days):
        try:
            ref_lang = await repo.get_lang(ref)
            await bot.send_message(ref, t(ref_lang, "ref_joined", days=cfg.ref_bonus_days))
        except Exception:
            pass


# ------------------------------------------------------------------ прогнозы
@router.message(Command("forecast"))
@router.message(F.text.in_(kb.BTN_FORECAST))
async def forecast(m: Message, repo: Repo, lang: str):
    u = await repo.get_user(m.from_user.id)
    if not u or not u["has_birth"]:
        return await m.answer(t(lang, "need_birth"))
    sign = {"moon": u["moon_rashi"], "sun_sid": u["sun_sid_rashi"], "sun_trop": u["sun_trop_sign"]}[u["sign_mode"]]
    if sign is None:
        return await m.answer(t(lang, "moon_unknown_mode"))
    s = settings_for(u["city_key"])
    now = datetime.now(ZoneInfo(u["tz"]))
    lun = await asyncio.to_thread(current_new_moon, now, s)
    facts = await asyncio.to_thread(lunation_facts, lun, s)
    text, kbd = rich(render_sign(facts, u["sign_mode"], sign, lang, u["city_key"]), lang)
    from .transits_handlers import transits_button
    from .why import why_button
    kbd.inline_keyboard[0].append(why_button("lun", lang))
    kbd.inline_keyboard.append([transits_button(lang)])
    await m.answer(text, reply_markup=kbd)


@router.message(Command("personal"))
@router.message(F.text.in_(kb.BTN_PERSONAL))
async def personal(m: Message, repo: Repo, cfg: Config, lang: str):
    u = await repo.get_user(m.from_user.id)
    if not is_premium(u, cfg):
        return await send_paywall(m, cfg, t(lang, "feat_personal"), lang=lang)
    prof = await repo.load_profile(m.from_user.id)
    if not prof:
        return await m.answer(t(lang, "need_birth"))
    if not prof.time_known or not prof.dashas:
        return await m.answer(t(lang, "need_time_personal"))
    txt = await asyncio.to_thread(personal_text, prof, datetime.now(ZoneInfo(u["tz"])), None, lang)
    text, kbd = rich(txt, lang)
    await m.answer(text, reply_markup=kbd)


@router.message(Command("me"))
@router.message(F.text.in_(kb.BTN_PROFILE))
async def me(m: Message, repo: Repo, lang: str):
    prof = await repo.load_profile(m.from_user.id)
    u = await repo.get_user(m.from_user.id)
    if not prof:
        return await m.answer(t(lang, "no_data"))
    from aiogram.types import InlineKeyboardButton
    chart_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t(lang, "kb_chart"),
                                                                           callback_data="chart:new")]])
    await m.answer(t(lang, "me_text", profile=describe_profile(prof, lang),
                     tnote="" if prof.time_known else t(lang, "time_not_given"),
                     mode=MODE_NAMES[lang][u["sign_mode"]], city=city_name(u["city_key"], lang)),
                   reply_markup=chart_kb)


# ------------------------------------------------------------------ настройки
@router.message(Command("settings"))
@router.message(F.text.in_(kb.BTN_SETTINGS))
async def settings(m: Message, repo: Repo, lang: str):
    u = await repo.get_user(m.from_user.id)
    await m.answer(t(lang, "settings"), reply_markup=kb.settings(bool(u and u["daily_push"]), lang))


@router.callback_query(F.data == "set:daily")
async def toggle_daily(c: CallbackQuery, repo: Repo, lang: str):
    u = await repo.get_user(c.from_user.id)
    if not u:
        return await c.answer()
    on = not u["daily_push"]
    await repo.set_daily_push(c.from_user.id, on)
    await c.message.edit_reply_markup(reply_markup=kb.settings(on, lang))
    await c.answer(t(lang, "daily_on" if on else "daily_off"))


@router.callback_query(F.data == "set:lang")
async def lang_menu(c: CallbackQuery):
    await c.message.answer("🌐 Язык / Language:", reply_markup=kb.languages())
    await c.answer()


@router.callback_query(F.data.startswith("lang:"))
async def set_lang(c: CallbackQuery, repo: Repo):
    new = c.data.split(":", 1)[1]
    if new not in ("ru", "en"):
        return await c.answer()
    await repo.ensure_user(c.from_user.id)
    await repo.set_lang(c.from_user.id, new)
    remember(c.from_user.id, new)
    await c.message.edit_text(t(new, "lang_set"))
    await c.message.answer(t(new, "welcome_back"), reply_markup=kb.main_menu(new))
    await c.answer()


@router.callback_query(F.data == "set:mode")
async def set_mode_menu(c: CallbackQuery, repo: Repo, lang: str):
    u = await repo.get_user(c.from_user.id)
    await c.message.answer(t(lang, "choose_mode"), reply_markup=kb.modes(bool(u and u["moon_rashi"] is not None), lang))
    await c.answer()


@router.callback_query(F.data.startswith("mode:"))
async def set_mode(c: CallbackQuery, repo: Repo, lang: str):
    mode = c.data.split(":", 1)[1]
    u = await repo.get_user(c.from_user.id)
    if mode == "moon" and (not u or u["moon_rashi"] is None):
        return await c.answer(t(lang, "need_time_short"), show_alert=True)
    await repo.set_mode(c.from_user.id, mode)
    sign = {"moon": u["moon_rashi"], "sun_sid": u["sun_sid_rashi"], "sun_trop": u["sun_trop_sign"]}[mode]
    await c.message.edit_text(t(lang, "mode_set", mode=MODE_NAMES[lang][mode], sign=SIGN[lang][sign],
                                btn=t(lang, "btn_forecast")))
    await c.answer()


@router.callback_query(F.data == "set:city")
async def set_city_menu(c: CallbackQuery, state: FSMContext, lang: str):
    await state.set_state(CityInput.name)
    await c.message.answer(t(lang, "choose_city"), reply_markup=kb.cities("city", lang))
    await c.answer()


@router.callback_query(F.data.startswith("city:"))
async def set_city(c: CallbackQuery, repo: Repo, state: FSMContext, lang: str):
    key = c.data.split(":", 1)[1]
    place = from_key(key, lang)
    if not place:
        return await c.answer()
    await state.clear()
    await repo.set_city(c.from_user.id, key, place[2])
    await c.message.edit_text(t(lang, "city_set", city=city_name(key, lang)))
    await c.answer()


@router.message(CityInput.name)
async def set_city_text(m: Message, repo: Repo, state: FSMContext, lang: str):
    place = await resolve_text(m, lang, "city")
    if place and place[4]:                    # для города расчёта нужен город, а не координаты
        await state.clear()
        await repo.set_city(m.from_user.id, place[4], place[2])
        await m.answer(t(lang, "city_set", city=place[3]))


@router.callback_query(F.data == "set:birth")
async def reset_birth(c: CallbackQuery, state: FSMContext, lang: str):
    await ask_date(c.message, state, lang)
    await c.answer()


@router.callback_query(F.data == "set:delete")
async def delete_menu(c: CallbackQuery, lang: str):
    await c.message.answer(t(lang, "delete_confirm"), reply_markup=kb.confirm_delete(lang))
    await c.answer()


@router.callback_query(F.data.startswith("del:"))
async def delete(c: CallbackQuery, repo: Repo, state: FSMContext, lang: str):
    if c.data == "del:yes":
        await repo.delete_user(c.from_user.id)
        forget(c.from_user.id)
        await state.clear()
        await c.message.edit_text(t(lang, "deleted"))
    else:
        await c.message.edit_text(t(lang, "cancelled"))
    await c.answer()


@router.message(Command("source"))
async def source(m: Message, cfg: Config, lang: str):
    """Ссылка на исходный код — требование AGPL-3.0 для сетевого сервиса."""
    await m.answer(t(lang, "source", url=cfg.source_url) if cfg.source_url else t(lang, "source_soon"),
                   disable_web_page_preview=True)


@router.message(Command("help"))
async def help_(m: Message, lang: str, cfg: Config):
    text = t(lang, "help")
    if cfg.free_mode:                        # бесплатный продукт: без Премиума и значков 💎
        text = "\n".join(x for x in text.split("\n") if not x.startswith("/premium")).replace(" 💎", "")
    await m.answer(text)
