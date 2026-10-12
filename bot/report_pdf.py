"""PDF-отчёт «Разбор натальной карты» (reportlab). Тексты — jyotish/report_texts*.py."""
from __future__ import annotations

import io
from html import escape

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer

import jyotish.report_texts as RU
import jyotish.report_texts_en as EN
from jyotish.natal import Chart
from jyotish.report import ChartReport
from jyotish.texts import HOUSE, KARAKA, NAKSHATRA_NAME, PLANET, REMEDY, SIGN, fmt_date, fmt_dt, ordinal_en

from .chart_view import BOLD_PATHS, FONT_PATHS, render_png

TX = {"ru": RU, "en": EN}
ACCENT, TEXT, MUTED = HexColor("#7A3E1D"), HexColor("#2B2B2B"), HexColor("#8A7A60")

_FONTS: tuple[str, str] | None = None


def _fonts() -> tuple[str, str]:
    """Регистрирует TTF с кириллицей (DejaVu на сервере, Segoe/Arial на Windows)."""
    global _FONTS
    if _FONTS:
        return _FONTS
    reg = bold = None
    for p in FONT_PATHS:
        try:
            pdfmetrics.registerFont(TTFont("KT", p))
            reg = "KT"
            break
        except Exception:
            continue
    for p in BOLD_PATHS:
        try:
            pdfmetrics.registerFont(TTFont("KT-Bold", p))
            bold = "KT-Bold"
            break
        except Exception:
            continue
    if reg:                                   # чтобы <b> в тексте давал жирное начертание
        from reportlab.lib.fonts import addMapping
        addMapping("KT", 0, 0, reg)
        addMapping("KT", 1, 0, bold or reg)
        addMapping("KT", 0, 1, reg)
        addMapping("KT", 1, 1, bold or reg)
    _FONTS = (reg or "Helvetica", bold or reg or "Helvetica-Bold")
    return _FONTS


def _styles():
    reg, bold = _fonts()
    return {
        "title": ParagraphStyle("t", fontName=bold, fontSize=24, leading=30, textColor=ACCENT, alignment=TA_CENTER),
        "sub": ParagraphStyle("s", fontName=reg, fontSize=12, leading=16, textColor=MUTED, alignment=TA_CENTER),
        "h1": ParagraphStyle("h1", fontName=bold, fontSize=16, leading=21, textColor=ACCENT, spaceBefore=10,
                             spaceAfter=6),
        "h2": ParagraphStyle("h2", fontName=bold, fontSize=11.5, leading=15, textColor=TEXT, spaceBefore=6,
                             spaceAfter=2),
        "p": ParagraphStyle("p", fontName=reg, fontSize=10.5, leading=15, textColor=TEXT, spaceAfter=4),
        "small": ParagraphStyle("sm", fontName=reg, fontSize=9, leading=12, textColor=MUTED, spaceAfter=3),
    }


def _ord(lang: str, h: int) -> str:
    return ordinal_en(h) if lang == "en" else str(h)


def _deg(lon: float) -> str:
    d = lon % 30
    return f"{int(d)}°{int((d % 1) * 60):02d}′"


def sections(r: ChartReport, lang: str) -> list[tuple[str, list[tuple[str, str]]]]:
    """Содержание отчёта: [(заголовок раздела, [(стиль, текст), ...])] — удобно тестировать без PDF."""
    T, S, P, N, H = TX[lang], SIGN[lang], PLANET[lang], NAKSHATRA_NAME[lang], HOUSE[lang]
    sec = T.SECTION
    out = []
    if r.time_known:
        out.append((sec["lagna"], [("h2", S[r.lagna]), ("p", T.LAGNA[r.lagna])]))
    else:
        out.append((sec["lagna"], [("p", sec["no_time"])]))
    out.append((sec["moon"], [("h2", f"{S[r.moon_rashi]} · {N[r.moon_nakshatra]}"),
                              ("p", T.MOON_SIGN[r.moon_rashi]), ("p", T.NAK_PERSON[r.moon_nakshatra])]))
    items = []
    for p in r.planets:
        head = f"{P[p.code]} — {S[p.rashi]} {_deg(p.lon)}, " + sec["in_house"].format(h=_ord(lang, p.house))
        items.append(("h2", head + (" (R)" if p.retro else "")))
        body = T.PLANET_HOUSE[p.code][p.house - 1]
        items.append(("p", body[:1].upper() + body[1:] + "."))
        if p.dignity:
            items.append(("p", T.DIGNITY[p.dignity].format(planet=P[p.code], karaka=KARAKA[lang][p.code])))
        if p.retro:
            items.append(("small", T.RETRO))
    out.append((sec["planets"], items))
    houses = []
    for h in range(1, 13):
        lord, w = r.house_lords[h]
        houses.append(("p", T.HOUSE_LORD.format(h=_ord(lang, h), lord=P[lord], w=_ord(lang, w), th=H[h], tw=H[w])))
    out.append((sec["houses"], houses))
    yog = []
    for y in r.yogas:
        title, text = T.YOGA[y.code]
        text = text.format(planets=", ".join(P[c] for c in y.planets),
                           house=_ord(lang, y.extra.get("house", 0)), **{"in": _ord(lang, y.extra.get("in", 0))})
        yog += [("h2", title), ("p", text)]
    out.append((sec["yogas"], yog or [("p", sec["no_yogas"])]))
    if r.dashas:
        das = []
        for d in r.dashas:
            line = sec["dasha_line"].format(lord=P[d.lord], start=fmt_date(d.start, lang), end=fmt_date(d.end, lang))
            das.append(("h2", line + (f" — {sec['current']}" if d.current else "")))
            ph = r.planet(d.lord).house
            das.append(("p", T.DASHA_LORD[d.lord][:1].upper() + T.DASHA_LORD[d.lord][1:] + ". " +
                        sec["dasha_in_chart"].format(planet=P[d.lord], h=_ord(lang, ph), theme=H[ph])))
        if r.antardasha:
            a = r.antardasha
            das.append(("small", f"{sec['antar']}: {P[a.lord]} ({fmt_date(a.start, lang)} – {fmt_date(a.end, lang)})"))
        out.append((sec["dashas"], das))
    up = []
    for code in r.weak:
        rm = REMEDY[lang][code]
        if lang == "en":
            up.append(("p", f"<b>{P[code]}</b> ({rm['day']}): mantra “{rm['mantra']}”, colour — {rm['color']}; "
                            f"charity — {rm['charity']}; practice — {rm['practice']}."))
        else:
            up.append(("p", f"<b>{P[code]}</b> ({rm['day']}): мантра «{rm['mantra']}», цвет — {rm['color']}; "
                            f"благотворительность — {rm['charity']}; практика — {rm['practice']}."))
    if up:
        out.append((sec["upaya"], up + [("small", sec["stones"])]))
    out.append((sec["about"], [("small", sec["method"])] + ([("small", sec["no_time"])] if not r.time_known else [])))
    return out


def build_pdf(ch: Chart, r: ChartReport, lang: str, place: str) -> bytes:
    st = _styles()
    T = TX[lang]
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm,
                            bottomMargin=16 * mm, title=T.SECTION["title"], author="Kai Tara")
    when = fmt_dt(ch.birth, lang) if r.time_known else fmt_date(ch.birth, lang)
    story = [Paragraph(escape(T.SECTION["title"]), st["title"]), Spacer(1, 4),
             Paragraph(escape(f"{when} · {place}"), st["sub"]),
             Paragraph(escape(T.SECTION["for"]), st["sub"]), Spacer(1, 10)]
    png = render_png(ch, lang, r.time_known, place)
    story += [Image(io.BytesIO(png), width=150 * mm, height=150 * mm), PageBreak()]
    for title, items in sections(r, lang):
        story.append(Paragraph(escape(title), st["h1"]))
        for style, text in items:
            safe = text if "<b>" in text else escape(text)
            story.append(Paragraph(safe, st[style]))
    doc.build(story, onFirstPage=_footer(lang), onLaterPages=_footer(lang))
    return buf.getvalue()


def _footer(lang: str):
    def draw(canvas, doc):
        reg, _ = _fonts()
        canvas.saveState()
        canvas.setFont(reg, 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(18 * mm, 10 * mm, "Kai Tara · @KaiTaraAstroBot")
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, str(doc.page))
        canvas.restoreState()
    return draw


def summary(r: ChartReport, lang: str) -> str:
    """Короткая выжимка для чата (бесплатно): лагна, Луна, текущая даша, число йог."""
    T, S, P, N = TX[lang], SIGN[lang], PLANET[lang], NAKSHATRA_NAME[lang]
    en = lang == "en"
    lines = [f"📄 <b>{'Your chart in brief' if en else 'Коротко о вашей карте'}</b>", ""]
    if r.time_known:
        lines.append(f"⬆️ <b>{S[r.lagna]}</b>: {T.LAGNA[r.lagna].split('. ')[0]}.")
    lines.append(f"🌙 <b>{S[r.moon_rashi]} · {N[r.moon_nakshatra]}</b>: {T.NAK_PERSON[r.moon_nakshatra].split(': ', 1)[-1]}")
    cur = next((d for d in r.dashas if d.current), None)
    if cur:
        lines.append(f"⏳ <b>{P[cur.lord]}</b>: {T.DASHA_LORD[cur.lord]}.")
    if r.yogas:
        names = ", ".join(T.YOGA[y.code][0] for y in r.yogas)
        lines.append(f"✨ {'Yogas' if en else 'Йоги'}: {names}.")
    lines += ["", ("The full PDF reading covers every planet, all 12 houses, yogas, dashas for decades ahead and "
                   "upayas." if en else
                   "В полном разборе (PDF) — каждая планета, все 12 домов, йоги, даши на десятилетия вперёд и упаи.")]
    return "\n".join(lines)
