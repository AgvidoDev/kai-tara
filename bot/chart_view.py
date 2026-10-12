"""Натальная карта: картинка в южноиндийском стиле (PNG) и таблица планет для Telegram.

Данные рождения используются только на время расчёта и нигде не сохраняются.
"""
from __future__ import annotations

import io
from datetime import datetime
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

from jyotish.core import from_jd, to_jd
from jyotish.natal import Chart, current_dasha
from jyotish.texts import NAKSHATRA_NAME, PLANET, SIGN, fmt_date, fmt_dt, house_label

ORDER = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]
ABBR = {
    "ru": {"Su": "Су", "Mo": "Лу", "Ma": "Ма", "Me": "Ме", "Ju": "Юп", "Ve": "Ве", "Sa": "Са", "Ra": "Ра", "Ke": "Ке",
           "As": "Лг"},
    "en": {"Su": "Su", "Mo": "Mo", "Ma": "Ma", "Me": "Me", "Ju": "Ju", "Ve": "Ve", "Sa": "Sa", "Ra": "Ra", "Ke": "Ke",
           "As": "Asc"},
}
# Южноиндийская сетка 4×4: знак → (столбец, строка). Знаки на местах, дома считаются от лагны.
CELL = {11: (0, 0), 0: (1, 0), 1: (2, 0), 2: (3, 0), 10: (0, 1), 3: (3, 1),
        9: (0, 2), 4: (3, 2), 8: (0, 3), 7: (1, 3), 6: (2, 3), 5: (3, 3)}

BG, LINE, TEXT, MUTED, ASC_BG, ACCENT = "#FBF7EF", "#8A6D3B", "#2B2B2B", "#9A8A70", "#F3E6C8", "#7A3E1D"
SIZE, PAD = 960, 30

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
]
BOLD_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


@lru_cache(maxsize=16)
def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for p in (BOLD_PATHS if bold else []) + FONT_PATHS:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def _center(d: ImageDraw.ImageDraw, box, text: str, font, fill=TEXT, dy: int = 0) -> None:
    x0, y0, x1, y1 = box
    w = d.textlength(text, font=font)
    d.text(((x0 + x1 - w) / 2, (y0 + y1) / 2 + dy), text, font=font, fill=fill, anchor="lm")


def render_png(ch: Chart, lang: str = "ru", time_known: bool = True, place: str = "") -> bytes:
    img = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(img)
    cell = (SIZE - 2 * PAD) / 4
    box = lambda c, r: (PAD + c * cell, PAD + r * cell, PAD + (c + 1) * cell, PAD + (r + 1) * cell)  # noqa: E731

    by_sign: dict[int, list[str]] = {}
    for code in ORDER:
        b = ch.planets[code]
        label = ABBR[lang][code] + ("ᴿ" if b.retro else "") + ("~" if code == "Mo" and not time_known else "")
        by_sign.setdefault(b.rashi, []).append(label)

    for sign, (c, r) in CELL.items():
        x0, y0, x1, y1 = box(c, r)
        is_asc = time_known and sign == ch.lagna_rashi
        d.rectangle((x0, y0, x1, y1), fill=ASC_BG if is_asc else BG, outline=LINE, width=3)
        d.text((x0 + 10, y1 - 8), SIGN[lang][sign], font=_font(19), fill=MUTED, anchor="ld")
        if is_asc:
            d.line((x0, y0 + cell * 0.32, x0 + cell * 0.32, y0), fill=ACCENT, width=3)
            d.text((x1 - 10, y0 + 8), ABBR[lang]["As"], font=_font(20, True), fill=ACCENT, anchor="ra")
        if time_known:
            h = (sign - ch.lagna_rashi) % 12 + 1
            d.text((x1 - 10, y1 - 8), str(h), font=_font(18), fill=MUTED, anchor="rd")
        items = by_sign.get(sign, [])
        rows = [items[i:i + 3] for i in range(0, len(items), 3)]
        f = _font(34 if len(items) <= 3 else 28, True)
        for i, row in enumerate(rows):
            _center(d, (x0, y0, x1, y1), "  ".join(row), f, dy=(i - (len(rows) - 1) / 2) * 42)

    # центр: подпись
    cx0, cy0, cx1, cy1 = PAD + cell, PAD + cell, PAD + 3 * cell, PAD + 3 * cell
    d.rectangle((cx0, cy0, cx1, cy1), fill=BG, outline=LINE, width=3)
    en = lang == "en"
    title = "Birth chart (Rashi)" if en else "Натальная карта (раши)"
    lines = [(title, _font(34, True), ACCENT),
             (fmt_dt(ch.birth, lang) if time_known else fmt_date(ch.birth, lang), _font(28), TEXT),
             (place, _font(24), TEXT),
             ("Lahiri ayanamsha · whole-sign houses" if en else "Айанамша Лахири · дома по знакам", _font(20), MUTED),
             ("" if time_known else ("No birth time: no Lagna" if en else "Без времени: лагна не определена"),
              _font(20), ACCENT),
             ("Kai Tara", _font(24, True), MUTED)]
    lines = [x for x in lines if x[0]]
    for i, (txt, f, col) in enumerate(lines):
        _center(d, (cx0, cy0, cx1, cy1), txt, f, fill=col, dy=(i - (len(lines) - 1) / 2) * 46)

    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def _deg(lon: float) -> str:
    d = lon % 30
    return f"{int(d)}°{int((d % 1) * 60):02d}′"


def render_text(ch: Chart, now: datetime, lang: str = "ru", time_known: bool = True) -> str:
    """Таблица планет: знак, градус, накшатра и пада, дом, ретроградность + текущие даши."""
    en = lang == "en"
    ref = ch.lagna_rashi if time_known else ch.moon_rashi
    S, N, P = SIGN[lang], NAKSHATRA_NAME[lang], PLANET[lang]
    out = [f"🪐 <b>{'Planets in your chart' if en else 'Планеты в вашей карте'}</b>", ""]
    if time_known:
        out.append(f"⬆️ <b>{'Lagna' if en else 'Лагна'}</b>: {S[ch.lagna_rashi]} {_deg(ch.asc)}")
    else:
        out.append("<i>" + ("Without a birth time the Lagna is unknown, so houses are counted from the Moon; "
                            "the Moon's position is for noon and may be off by up to 7°."
                            if en else "Без времени рождения лагна неизвестна — дома считаются от Луны; положение "
                            "Луны дано на полдень и может отличаться до 7°.") + "</i>")
    for code in ORDER:
        b = ch.planets[code]
        h = (b.rashi - ref) % 12 + 1
        retro = " (R)" if b.retro else ""
        if en:
            out.append(f"• <b>{P[code]}</b>{retro}: {S[b.rashi]} {_deg(b.lon)}, {N[b.nakshatra]} nakshatra "
                       f"(pada {b.pada}), {house_label('en', h)}")
        else:
            out.append(f"• <b>{P[code]}</b>{retro}: {S[b.rashi]} {_deg(b.lon)}, накшатра {N[b.nakshatra]} "
                       f"({b.pada} пада), {h}-й дом")
    if time_known:
        md, ad = current_dasha(ch.dashas, to_jd(now))
        zone = ch.loc.zone
        span = lambda x: f"{fmt_date(from_jd(x.start, zone), lang)} – {fmt_date(from_jd(x.end, zone), lang)}"  # noqa: E731
        out += ["", f"⏳ <b>{'Mahadasha' if en else 'Махадаша'}</b>: {P[md.lord]} ({span(md)})"]
        if ad:
            out.append(f"⏳ <b>{'Antardasha' if en else 'Антардаша'}</b>: {P[ad.lord]} ({span(ad)})")
    out += ["", "🔒 " + ("Your birth data was used only for this calculation and has not been saved." if en else
                        "Данные рождения использованы только для этого расчёта и не сохранены."),
            "<i>" + ("This forecast is for information only." if en else "Прогноз носит ознакомительный характер.") + "</i>"]
    return "\n".join(out)
