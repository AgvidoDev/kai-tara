"""Персональный прогноз на 30 дней в PDF — по сохранённому профилю (дата рождения не нужна)."""
from __future__ import annotations

import asyncio
import io
from datetime import date, datetime, timedelta
from html import escape
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardButton, Message
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from jyotish.core import Settings
from jyotish.daily import advice
from jyotish.muhurta import CATEGORIES as CAL_CATEGORIES, build_calendar
from jyotish.profile import AstroProfile
from jyotish.texts import (CAL_CATEGORY, HOUSE, LUNATION_ADVICE, NAKSHATRA_NAME, PLANET, SIGN, SPECIAL, TONE,
                           WEEKDAY_SHORT, event_text, fmt_date, house_label)

from .i18n import t
from .period_view import build_period
from .report_pdf import _fonts, _footer, _styles

DAYS = 30
router = Router()
GRID, HEAD_BG = HexColor("#D9CDB4"), HexColor("#F3E6C8")
TONE_BG = {"good": HexColor("#E3F1DF"), "bad": HexColor("#F6E0DC")}   # в PDF без эмодзи — шрифт их не содержит


def _dasha_texts(lang: str):
    import jyotish.report_texts as RU
    import jyotish.report_texts_en as EN
    return (EN if lang == "en" else RU).DASHA_LORD


def _day(d: date, lang: str) -> str:
    return f"{fmt_date(d, lang, year=False)} {WEEKDAY_SHORT[lang][d.weekday()]}"


def build_month_pdf(start: date, s: Settings, prof: AstroProfile, place: str, transits: list[str],
                    lang: str) -> bytes:
    en = lang == "en"
    st = _styles()
    reg, _ = _fonts()
    end = start + timedelta(days=DAYS - 1)
    per = build_period(start, end, s, prof.moon_rashi, prof.moon_nakshatra)
    cal = build_calendar(start, DAYS, prof.moon_rashi, prof.moon_nakshatra, s)
    P, S, N = PLANET[lang], SIGN[lang], NAKSHATRA_NAME[lang]
    story = [Paragraph(escape("Personal forecast for 30 days" if en else "Персональный прогноз на 30 дней"),
                       st["title"]), Spacer(1, 4),
             Paragraph(escape(f"{fmt_date(start, lang)} – {fmt_date(end, lang)} · {place}"), st["sub"]),
             Paragraph("Kai Tara", st["sub"]), Spacer(1, 12)]

    # 1. Главное
    story.append(Paragraph(escape("The main themes" if en else "Главное на месяц"), st["h1"]))
    sign = prof.moon_rashi if prof.moon_rashi is not None else prof.sun_sid_rashi
    md, ad = prof.current_dasha(datetime.combine(start, datetime.min.time()))
    dl = _dasha_texts(lang)
    if md:
        story.append(Paragraph(f"<b>{'Mahadasha' if en else 'Махадаша'} {P[md.lord]}</b>: "
                               f"{escape(dl[md.lord])}.", st["p"]))
    if ad:
        story.append(Paragraph(f"<b>{'Antardasha' if en else 'Антардаша'} {P[ad.lord]}</b> "
                               f"({'until' if en else 'до'} {ad.end[5:]}.{ad.end[:4]}): {escape(dl[ad.lord])}.",
                               st["p"]))
    for dt, e in per.events:
        if e.kind in ("new_moon", "full_moon"):
            h = (e.rashi - sign) % 12 + 1
            name = event_text(lang, e.as_dict())
            story.append(Paragraph(f"<b>{_day(dt.date(), lang)} — {escape(name)}</b>, "
                                   f"{house_label(lang, h)} ({escape(HOUSE[lang][h])}): "
                                   f"{escape(LUNATION_ADVICE[lang][h])}.", st["p"]))
    if transits:
        story.append(Paragraph(f"<b>{'Major transits' if en else 'Большие транзиты'}</b>: " +
                               escape("; ".join(transits)), st["p"]))
    good = sorted([p for p in per.days if p.score >= 2], key=lambda p: p.info.day)
    hard = sorted([p for p in per.days if p.score <= -2], key=lambda p: p.info.day)
    if good:
        story.append(Paragraph(f"<b>{'Best days' if en else 'Лучшие дни'}</b>: " +
                               ", ".join(_day(p.info.day, lang) for p in good), st["p"]))
    if hard:
        story.append(Paragraph(f"<b>{'Take it easy' if en else 'Поберегите силы'}</b>: " +
                               ", ".join(_day(p.info.day, lang) for p in hard), st["p"]))
    basis = (f"Based on your Moon sign ({S[sign]})" if en else f"Расчёт от вашей Луны ({S[sign]})") + (
        f", birth nakshatra {N[prof.moon_nakshatra]}" if en and prof.moon_nakshatra is not None else
        f", накшатра рождения {N[prof.moon_nakshatra]}" if prof.moon_nakshatra is not None else "") + "."
    story.append(Paragraph(escape(basis), st["small"]))

    # 2. Дни
    story.append(Paragraph(escape("Day by day" if en else "По дням"), st["h1"]))
    cell = lambda x: Paragraph(escape(x), st["small"])  # noqa: E731
    rows = [[cell("Date" if en else "Дата"), cell("Day" if en else "День"),
             cell("Moon's nakshatra" if en else "Накшатра Луны"), cell("Good for" if en else "Хорошо для")]]
    for p in per.days:
        do, _ = advice(p, lang)
        extra = "; ".join(SPECIAL[lang][c].split(" — ")[0] for c in p.info.special)
        rows.append([cell(_day(p.info.day, lang)), cell(TONE[lang][p.tone]),
                     cell(N[p.info.nakshatra]), cell(do[0] + (f" · {extra}" if extra else ""))])
    tbl = Table(rows, colWidths=[24 * mm, 30 * mm, 34 * mm, 86 * mm], repeatRows=1)
    style = [("FONT", (0, 0), (-1, -1), reg, 8), ("BACKGROUND", (0, 0), (-1, 0), HEAD_BG),
             ("GRID", (0, 0), (-1, -1), 0.4, GRID), ("VALIGN", (0, 0), (-1, -1), "TOP")]
    for i, p in enumerate(per.days, start=1):
        if p.tone in TONE_BG:
            style.append(("BACKGROUND", (1, i), (1, i), TONE_BG[p.tone]))
    tbl.setStyle(TableStyle(style))
    story.append(tbl)

    # 3. Благоприятные дни по темам
    story.append(Paragraph(escape("Favourable days by topic" if en else "Благоприятные дни по темам"), st["h1"]))
    for c in CAL_CATEGORIES:
        days = cal.best.get(c.key) or []
        txt = ", ".join(_day(p.info.day, lang) for p in days) or ("no suitable days" if en else "подходящих дней нет")
        story.append(Paragraph(f"<b>{escape(CAL_CATEGORY[lang][c.key])}</b>: {escape(txt)}", st["p"]))

    # 4. События неба
    if per.events:
        story.append(Paragraph(escape("Sky events" if en else "События неба"), st["h1"]))
        for dt, e in per.events:
            story.append(Paragraph(f"{_day(dt.date(), lang)} {dt:%H:%M} — {escape(event_text(lang, e.as_dict()))}",
                                   st["p"]))

    # 5. Упаи и методика
    from .astro_service import remedy_line
    focus = [x for x in ([md.lord] if md else []) + ([ad.lord] if ad and (not md or ad.lord != md.lord) else [])]
    if focus:
        story.append(Paragraph(escape("Upayas" if en else "Упаи"), st["h1"]))
        for code in focus:
            story.append(Paragraph(remedy_line(code, lang).lstrip("• "), st["p"]))
    story.append(Paragraph(escape("About the calculation" if en else "О расчёте"), st["h1"]))
    story.append(Paragraph(escape(
        "Sidereal zodiac, Lahiri ayanamsha; days are rated by Tara Bala (from your birth nakshatra), Chandra Bala "
        "(the Moon's house from your natal Moon) and the tithi. This forecast is for information only."
        if en else
        "Сидерический зодиак, айанамша Лахири; дни оцениваются по тара-бале (от вашей накшатры рождения), "
        "чандра-бале (дом Луны от натальной) и титхи. Прогноз носит ознакомительный характер."), st["small"]))

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm,
                            bottomMargin=16 * mm, title="Kai Tara", author="Kai Tara")
    doc.build(story, onFirstPage=_footer(lang), onLaterPages=_footer(lang))
    return buf.getvalue()


def pdf30_button(lang: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=t(lang, "kb_pdf30"), callback_data="pdf30")


async def _send(m: Message, tg_id: int, repo, cfg, lang: str) -> None:
    from jyotish.core import city_name

    from .astro_service import settings_for
    from .payments import is_premium, send_paywall
    from .transits_handlers import current
    from .transits_view import short_title
    u = await repo.get_user(tg_id)
    prof = await repo.load_profile(tg_id)
    if not u or not prof:
        await m.answer(t(lang, "need_birth"))
        return
    if not is_premium(u, cfg):
        await send_paywall(m, cfg, t(lang, "feat_pdf30"), lang=lang)
        return
    await m.answer(t(lang, "report_making"))
    today = datetime.now(ZoneInfo(u["tz"])).date()
    tr = [short_title(x, lang) for x in await asyncio.to_thread(current)]
    pdf = await asyncio.to_thread(build_month_pdf, today, settings_for(u["city_key"]), prof,
                                  city_name(u["city_key"], lang), tr, lang)
    await m.answer_document(BufferedInputFile(pdf, "kai_tara_30_days.pdf"), caption=t(lang, "pdf30_caption"))


@router.message(Command("pdf30"))
async def pdf30_cmd(m: Message, repo, cfg, lang: str):
    await _send(m, m.from_user.id, repo, cfg, lang)


@router.callback_query(F.data == "pdf30")
async def pdf30_cb(c: CallbackQuery, repo, cfg, lang: str):
    await c.answer()
    await _send(c.message, c.from_user.id, repo, cfg, lang)
