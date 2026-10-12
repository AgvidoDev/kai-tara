"""Годовой прогноз (Варшапхала) в PDF: по данным карты из памяти бота (/chart), без сохранения даты рождения."""
from __future__ import annotations

import asyncio
import io
from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardButton, Message
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

import jyotish.report_texts as RU
import jyotish.report_texts_en as EN
from jyotish.core import RASHI
from jyotish.texts import HOUSE, PLANET, SIGN, fmt_date, fmt_dt
from jyotish.varsha import Varsha
from jyotish.varsha_texts import MUNTHA, SECTION, YEAR_LAGNA, planet_effect

from .i18n import t
from .report_pdf import _footer, _ord, _styles

router = Router()
ORDER = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:]


def sections(v: Varsha, now: datetime, lang: str) -> list[tuple[str, list[tuple[str, str]]]]:
    """Содержание прогноза: [(заголовок, [(стиль, текст), ...])] — тестируется без PDF."""
    sec, S, P, H = SECTION[lang], SIGN[lang], PLANET[lang], HOUSE[lang]
    dl = (EN if lang == "en" else RU).DASHA_LORD
    out = []

    main = [("p", sec["solar"].format(when=fmt_dt(v.start, lang) if v.time_known else fmt_date(v.start, lang)))]
    mh = v.muntha_house
    main.append(("p", f"<b>{escape(sec['muntha_short'].format(sign=S[v.muntha], h=_ord(lang, mh)))}</b> — "
                      f"{escape(sec['quality'][v.muntha_quality])}."))
    cur = v.current_mudda(now)
    if cur:
        main.append(("p", f"<b>{escape(P[cur.lord])}</b> ({sec['now']}, {fmt_date(cur.start, lang)} – "
                          f"{fmt_date(cur.end, lang)}): {escape(dl[cur.lord])}."))
    if not v.time_known:
        main.append(("small", sec["no_time"]))
    out.append((sec["main"], main))

    if v.lagna_rashi is not None:
        out.append((sec["lagna"], [("h2", S[v.lagna_rashi]), ("p", YEAR_LAGNA[lang][v.lagna_rashi])]))

    out.append((sec["muntha"], [("h2", sec["muntha_short"].format(sign=S[v.muntha], h=_ord(lang, mh))), ("p", MUNTHA[lang][mh - 1])]))

    lords = []
    if v.lagna_rashi is not None:
        lord = RASHI[v.lagna_rashi]["lord"]
        h = v.house(v.planets[lord].rashi)
        lords.append(("p", sec["lagna_lord"].format(planet=P[lord], h=_ord(lang, h), theme=H[h])))
    lord = RASHI[v.muntha]["lord"]
    h = v.house(v.planets[lord].rashi)
    lords.append(("p", sec["muntha_lord"].format(planet=P[lord], h=_ord(lang, h), theme=H[h])))
    out.append((sec["lords"], lords))

    pl = []
    for code in ORDER:
        b = v.planets[code]
        h = v.house(b.rashi)
        pl.append(("p", sec["planet_line"].format(planet=P[code], sign=S[b.rashi], h=_ord(lang, h), theme=H[h]) +
                   " " + _cap(planet_effect(lang, code, h)) + "."))
    out.append((sec["planets"], pl))

    md = []
    for p in v.mudda:
        line = sec["mudda_line"].format(lord=P[p.lord], start=fmt_date(p.start, lang), end=fmt_date(p.end, lang))
        md.append(("h2", line + (f" — {sec['now']}" if p is cur else "")))
        md.append(("p", _cap(dl[p.lord]) + "."))
    out.append((sec["mudda"], md))

    tr = [("p", sec["ingress"].format(date=fmt_date(i.when, lang), planet=P[i.code], sign=S[i.rashi],
                                      h=_ord(lang, v.house(i.rashi)), theme=H[v.house(i.rashi)]) +
           (sec["retro"] if i.retro else ""))
          for i in v.ingresses]
    out.append((sec["transits"], tr or [("p", sec["no_transits"])]))
    out.append((sec["about"], [("small", sec["method"])]))
    return out


def build_varsha_pdf(v: Varsha, now: datetime, lang: str, place: str) -> bytes:
    st = _styles()
    sec = SECTION[lang]
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm,
                            bottomMargin=16 * mm, title=sec["title"], author="Kai Tara")
    story = [Paragraph(escape(sec["title"]), st["title"]), Spacer(1, 4),
             Paragraph(escape(sec["year"].format(n=v.age + 1, start=fmt_date(v.start, lang),
                                                 end=fmt_date(v.end, lang)) + f" · {place}"), st["sub"]),
             Paragraph(escape(sec["for"]), st["sub"]), Spacer(1, 10)]
    for title, items in sections(v, now, lang):
        story.append(Paragraph(escape(title), st["h1"]))
        for style, text in items:
            story.append(Paragraph(text if "<b>" in text else escape(text), st[style]))
    doc.build(story, onFirstPage=_footer(lang), onLaterPages=_footer(lang))
    return buf.getvalue()


def varsha_button(lang: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=t(lang, "kb_varsha"), callback_data="varsha:get")


async def _send(m: Message, tg_id: int, state: FSMContext, repo, cfg, lang: str) -> None:
    from jyotish.core import Location, Settings
    from jyotish.natal import build_chart
    from jyotish.varsha import build_varsha

    from .payments import is_premium, send_paywall
    from .report_flow import pending_chart

    chart = await pending_chart(state)
    if not chart:
        await m.answer(t(lang, "varsha_need_chart"))
        return
    u = await repo.get_user(tg_id)
    if not is_premium(u, cfg):
        await send_paywall(m, cfg, t(lang, "feat_varsha"), lang=lang)
        return
    await m.answer(t(lang, "report_making"))
    loc = Location(chart["place"], chart["lat"], chart["lon"], chart["tz"])
    zone = ZoneInfo(chart["tz"])
    birth = datetime.strptime(f"{chart['date']} {chart['time']}", "%Y-%m-%d %H:%M").replace(tzinfo=zone)

    def work() -> bytes:
        s = Settings(location=loc)
        now = datetime.now(zone)
        v = build_varsha(build_chart(birth, loc, s), now, chart["known"], s)
        return build_varsha_pdf(v, now, lang, chart["place"])

    pdf = await asyncio.to_thread(work)
    # данные остаются в памяти до истечения 30 минут — чтобы можно было взять и разбор карты
    await m.answer_document(BufferedInputFile(pdf, "kai_tara_year.pdf"), caption=t(lang, "varsha_caption"))


@router.message(Command("varsha"))
async def varsha_cmd(m: Message, state: FSMContext, repo, cfg, lang: str):
    await _send(m, m.from_user.id, state, repo, cfg, lang)


@router.callback_query(F.data == "varsha:get")
async def varsha_cb(c: CallbackQuery, state: FSMContext, repo, cfg, lang: str):
    await c.answer()
    await _send(c.message, c.from_user.id, state, repo, cfg, lang)
