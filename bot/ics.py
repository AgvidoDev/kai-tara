"""Выгрузка астрокалендаря в .ics (Google / Apple / Outlook): события неба и личные даты на 90 дней."""
from __future__ import annotations

import asyncio
import hashlib
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardButton, Message

from jyotish.core import Settings
from jyotish.texts import PLANET, SPECIAL, TONE, event_text

from .i18n import t

DAYS = 90
router = Router()


def _esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _fold(line: str) -> str:
    """RFC 5545: строки не длиннее 75 октетов, перенос — пробел в начале следующей."""
    out, cur = [], ""
    for ch in line:
        if len((cur + ch).encode("utf-8")) > 74:
            out.append(cur)
            cur = " " + ch
        else:
            cur += ch
    out.append(cur)
    return "\r\n".join(out)


def _uid(*parts: str) -> str:
    return hashlib.sha1("|".join(parts).encode()).hexdigest()[:20] + "@kaitara"


def build_ics(start: date, s: Settings, natal_moon: int | None, natal_nak: int | None, profile, lang: str) -> bytes:
    from .period_view import build_period
    per = build_period(start, start + timedelta(days=DAYS - 1), s, natal_moon, natal_nak)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ev: list[list[str]] = []

    def timed(dt: datetime, title: str, key: str):
        u = dt.astimezone(timezone.utc)
        ev.append(["BEGIN:VEVENT", f"UID:{_uid(key, u.isoformat())}", f"DTSTAMP:{stamp}",
                   f"DTSTART:{u:%Y%m%dT%H%M%SZ}", f"DTEND:{(u + timedelta(minutes=30)):%Y%m%dT%H%M%SZ}",
                   f"SUMMARY:{_esc(title)}", "END:VEVENT"])

    def allday(d: date, title: str, key: str, desc: str = ""):
        ev.append(["BEGIN:VEVENT", f"UID:{_uid(key, d.isoformat())}", f"DTSTAMP:{stamp}",
                   f"DTSTART;VALUE=DATE:{d:%Y%m%d}", f"DTEND;VALUE=DATE:{(d + timedelta(days=1)):%Y%m%d}",
                   f"SUMMARY:{_esc(title)}"] + ([f"DESCRIPTION:{_esc(desc)}"] if desc else []) +
                  ["TRANSP:TRANSPARENT", "END:VEVENT"])

    for dt, e in per.events:
        timed(dt, f"🪐 {event_text(lang, e.as_dict())}", "sky")
    for p in per.days:
        for code in p.info.special:
            if code == "ekadashi":
                allday(p.info.day, f"🙏 {SPECIAL[lang]['ekadashi'].split(' — ')[0]}", "ekadashi",
                       SPECIAL[lang]["ekadashi"])
        if p.score >= 2:
            allday(p.info.day, f"🟢 Kai Tara: {TONE[lang]['good']}", "good",
                   "Tara Bala + Chandra Bala" if lang == "en" else "Тара-бала + чандра-бала")
    if profile and profile.dashas:
        now = datetime.now(timezone.utc)
        md, ad = profile.current_dasha(now)
        if ad:
            y, m = int(ad.end[:4]), int(ad.end[5:7])
            d = date(y, m, 1)
            if start <= d <= start + timedelta(days=DAYS):
                P = PLANET[lang]
                allday(d, ("⏳ Antardasha changes" if lang == "en" else "⏳ Смена антардаши") +
                       f": {P[ad.lord]} → …", "dasha")
    name = "Kai Tara — astro calendar" if lang == "en" else "Kai Tara — астрокалендарь"
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Kai Tara//Astro Calendar//RU", "CALSCALE:GREGORIAN",
             "METHOD:PUBLISH", f"X-WR-CALNAME:{_esc(name)}"]
    for block in ev:
        lines += block
    lines.append("END:VCALENDAR")
    return ("\r\n".join(_fold(x) for x in lines) + "\r\n").encode("utf-8")


def ics_button(lang: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=t(lang, "kb_ics"), callback_data="ics:get")


async def _send(m: Message, tg_id: int, repo, cfg, lang: str) -> None:
    from .astro_service import settings_for
    from .payments import is_premium, send_paywall
    u = await repo.get_user(tg_id)
    if not u or not u["has_birth"]:
        await m.answer(t(lang, "need_birth"))
        return
    if not is_premium(u, cfg):
        await send_paywall(m, cfg, t(lang, "feat_ics"), lang=lang)
        return
    prof = await repo.load_profile(tg_id)
    today = datetime.now(ZoneInfo(u["tz"])).date()
    data = await asyncio.to_thread(build_ics, today, settings_for(u["city_key"]), u["moon_rashi"],
                                   u["moon_nakshatra"], prof, lang)
    await m.answer_document(BufferedInputFile(data, "kai_tara.ics"), caption=t(lang, "ics_caption"))


@router.message(Command("ics"))
async def ics_cmd(m: Message, repo, cfg, lang: str):
    await _send(m, m.from_user.id, repo, cfg, lang)


@router.callback_query(F.data == "ics:get")
async def ics_cb(c: CallbackQuery, repo, cfg, lang: str):
    await c.answer()
    await _send(c.message, c.from_user.id, repo, cfg, lang)
