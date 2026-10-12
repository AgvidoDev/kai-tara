"""Прогноз на 7 дней и на календарный месяц: дни с личной оценкой + события неба."""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from html import escape

from jyotish.core import Settings, from_jd, to_jd
from jyotish.daily import PersonalDay, advice, day_info, personal_day
from jyotish.events import Event, all_events
from jyotish.texts import NAKSHATRA_NAME, PLANET, SPECIAL, TONE, WEEKDAY_SHORT, event_text, fmt_date

DISCLAIMER = {"ru": "<i>Прогноз носит ознакомительный характер.</i>",
              "en": "<i>This forecast is for information only.</i>"}


@dataclass
class Period:
    start: date
    end: date                         # включительно
    days: list[PersonalDay]
    events: list[tuple[datetime, Event]]


def build_period(start: date, end: date, s: Settings, natal_moon: int | None, natal_nak: int | None) -> Period:
    days = [personal_day(day_info(start + timedelta(days=i), s), natal_moon, natal_nak)
            for i in range((end - start).days + 1)]
    zone = s.location.zone
    jd0 = to_jd(datetime.combine(start, time(0, 0), tzinfo=zone))
    jd1 = to_jd(datetime.combine(end + timedelta(days=1), time(0, 0), tzinfo=zone))
    events = [(from_jd(e.jd, zone), e) for e in all_events(jd0, jd1, s)]
    return Period(start, end, days, events)


def month_bounds(today: date) -> tuple[date, date]:
    last = calendar.monthrange(today.year, today.month)[1]
    return today, date(today.year, today.month, last)


def _label(d: date, lang: str) -> str:
    return f"{fmt_date(d, lang, year=False)} ({WEEKDAY_SHORT[lang][d.weekday()]})"


def _events_block(per: Period, lang: str) -> list[str]:
    if not per.events:
        return []
    title = "📅 <b>Sky events</b>" if lang == "en" else "📅 <b>События неба</b>"
    return ["", title] + [f"• {_label(dt.date(), lang)} {dt:%H:%M} — "
                          f"{escape(event_text(lang, e.as_dict()))}" for dt, e in per.events]


def render_week(per: Period, lang: str, place: str) -> str:
    en = lang == "en"
    title = "Your next 7 days" if en else "Ваши 7 дней"
    out = [f"📆 <b>{title}: {fmt_date(per.start, lang, False)} – {fmt_date(per.end, lang, False)}</b> "
           f"({escape(place)})", ""]
    for p in per.days:
        nak = NAKSHATRA_NAME[lang][p.info.nakshatra]
        do, _ = advice(p, lang)
        line = f"{p.icon} <b>{_label(p.info.day, lang)}</b> — {TONE[lang][p.tone]}, {nak}"
        out.append(line)
        out.append(f"   {escape(do[0])}")
        for code in p.info.special:
            out.append(f"   ✨ {SPECIAL[lang][code]}")
    best = max(per.days, key=lambda p: (p.score, -p.info.day.toordinal()))
    worst = min(per.days, key=lambda p: (p.score, p.info.day.toordinal()))
    out.append("")
    out.append(f"⭐ {'Best day' if en else 'Лучший день'}: <b>{_label(best.info.day, lang)}</b>")
    if worst.score < 0:
        out.append(f"⚠️ {'Take it easy on' if en else 'Поберегите силы'}: <b>{_label(worst.info.day, lang)}</b>")
    out += _events_block(per, lang)
    out += ["", DISCLAIMER[lang]]
    return "\n".join(out)


def render_month(per: Period, lang: str, place: str, dasha_line: str = "", transits: list[str] | None = None) -> str:
    en = lang == "en"
    title = f"Month ahead: until {fmt_date(per.end, lang, False)}" if en else \
        f"Месяц: до {fmt_date(per.end, lang, False)}"
    out = [f"🗓 <b>{title}</b> ({escape(place)})", ""]
    good = sorted([p for p in per.days if p.score >= 1], key=lambda p: (-p.score, p.info.day))[:5]
    hard = sorted([p for p in per.days if p.score <= -1], key=lambda p: (p.score, p.info.day))[:5]
    if good:
        out.append(f"🟢 <b>{'Your best days' if en else 'Ваши лучшие дни'}</b>: " +
                   ", ".join(_label(p.info.day, lang) for p in sorted(good, key=lambda p: p.info.day)))
    if hard:
        out.append(f"🔴 <b>{'Take it easy' if en else 'Поберегите силы'}</b>: " +
                   ", ".join(_label(p.info.day, lang) for p in sorted(hard, key=lambda p: p.info.day)))
    specials = [(p.info.day, c) for p in per.days for c in p.info.special if c in ("ekadashi", "amavasya", "purnima")]
    if specials:
        out += ["", f"✨ <b>{'Special days' if en else 'Особые дни'}</b>"]
        out += [f"• {_label(d, lang)} — {SPECIAL[lang][c].split(' — ')[0]}" for d, c in specials]
    if dasha_line:
        out += ["", dasha_line]
    if transits:
        out += ["", f"🐉 <b>{'Major transits in effect' if en else 'Действующие большие транзиты'}</b>"] + \
               [f"• {escape(x)}" for x in transits]
    out += _events_block(per, lang)
    out += ["", ("Details for any day: ☀️ Today; favourable days by topic: 📅 Calendar." if en else
                 "Подробно о любом дне — ☀️ Сегодня; благоприятные дни по темам — 📅 Календарь."),
            "", DISCLAIMER[lang]]
    return "\n".join(out)


def dasha_text(md, ad, lang: str) -> str:
    if not md:
        return ""
    P = PLANET[lang]
    if lang == "en":
        s = f"⏳ Mahadasha <b>{P[md.lord]}</b>"
        return s + (f", antardasha <b>{P[ad.lord]}</b> (until {ad.end[5:]}.{ad.end[:4]})" if ad else "")
    s = f"⏳ Махадаша <b>{P[md.lord]}</b>"
    return s + (f", антардаша <b>{P[ad.lord]}</b> (до {ad.end[5:]}.{ad.end[:4]})" if ad else "")


# ------------------------------------------------------------------ обработчики
from aiogram import F, Router  # noqa: E402
from aiogram.filters import Command  # noqa: E402
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message  # noqa: E402

router = Router()


def period_buttons(lang: str) -> list[InlineKeyboardButton]:
    from .i18n import t
    return [InlineKeyboardButton(text=t(lang, "kb_week"), callback_data="per:week"),
            InlineKeyboardButton(text=t(lang, "kb_month"), callback_data="per:month")]


async def _send_period(m: Message, tg_id: int, kind: str, repo, cfg, lang: str) -> None:
    import asyncio
    from zoneinfo import ZoneInfo

    from jyotish.core import city_name

    from .astro_service import settings_for
    from .glossary import linkify, terms_button
    from .i18n import t
    from .payments import is_premium, send_paywall
    u = await repo.get_user(tg_id)
    if not u or not u["has_birth"]:
        await m.answer(t(lang, "need_birth"))
        return
    if not is_premium(u, cfg):
        await send_paywall(m, cfg, t(lang, "feat_week" if kind == "week" else "feat_month"), lang=lang)
        return
    s = settings_for(u["city_key"])
    today = datetime.now(ZoneInfo(u["tz"])).date()
    place = city_name(u["city_key"], lang)
    if kind == "week":
        per = await asyncio.to_thread(build_period, today, today + timedelta(days=6), s,
                                      u["moon_rashi"], u["moon_nakshatra"])
        text = render_week(per, lang, place)
    else:
        a, b = month_bounds(today)
        if (b - a).days < 6:                       # конец месяца — показываем и следующий
            nxt = b + timedelta(days=1)
            b = month_bounds(nxt)[1]
        per = await asyncio.to_thread(build_period, a, b, s, u["moon_rashi"], u["moon_nakshatra"])
        prof = await repo.load_profile(tg_id)
        md, ad = prof.current_dasha(datetime.now(ZoneInfo(u["tz"]))) if prof and prof.dashas else (None, None)
        from .transits_handlers import current
        from .transits_view import short_title
        tr = [short_title(x, lang) for x in await asyncio.to_thread(current)]
        text = render_month(per, lang, place, dasha_text(md, ad, lang), tr)
    rows = [[terms_button(lang)]]
    if kind == "month":
        from .ics import ics_button
        from .month_pdf import pdf30_button
        rows.append([ics_button(lang), pdf30_button(lang)])
    await m.answer(linkify(text, lang=lang), reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


@router.message(Command("week"))
async def week_cmd(m: Message, repo, cfg, lang: str):
    await _send_period(m, m.from_user.id, "week", repo, cfg, lang)


@router.message(Command("month"))
async def month_cmd(m: Message, repo, cfg, lang: str):
    await _send_period(m, m.from_user.id, "month", repo, cfg, lang)


@router.callback_query(F.data.in_({"per:week", "per:month"}))
async def period_cb(c: CallbackQuery, repo, cfg, lang: str):
    await c.answer()
    await _send_period(c.message, c.from_user.id, c.data.split(":")[1], repo, cfg, lang)
