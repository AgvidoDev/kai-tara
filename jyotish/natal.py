"""Натальная карта и Вимшоттари-даша для персональных прогнозов."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .core import Body, Location, Settings, from_jd, lagna, positions, to_jd
from .kb import NAKSHATRA, PLANET_RU, RASHI, VIMSHOTTARI_ORDER, VIMSHOTTARI_YEARS

YEAR_DAYS = 365.2425
NAK_SPAN = 360 / 27


@dataclass
class Dasha:
    lord: str
    start: float  # jd
    end: float
    sub: list["Dasha"] | None = None

    def label(self, tz) -> str:
        return f"{PLANET_RU[self.lord]}: {from_jd(self.start, tz):%d.%m.%Y} – {from_jd(self.end, tz):%d.%m.%Y}"


def vimshottari(moon_lon: float, birth_jd: float, levels: int = 2) -> list[Dasha]:
    nak = int(moon_lon // NAK_SPAN)
    lord = NAKSHATRA[nak]["lord"]
    passed = (moon_lon % NAK_SPAN) / NAK_SPAN
    i = VIMSHOTTARI_ORDER.index(lord)
    start = birth_jd - passed * VIMSHOTTARI_YEARS[lord] * YEAR_DAYS
    out = []
    for k in range(9 + 1):  # 120 лет + запас
        l = VIMSHOTTARI_ORDER[(i + k) % 9]
        end = start + VIMSHOTTARI_YEARS[l] * YEAR_DAYS
        d = Dasha(l, start, end)
        if levels > 1:
            d.sub = _sub(d)
        out.append(d)
        start = end
    return out


def _sub(md: Dasha) -> list[Dasha]:
    i = VIMSHOTTARI_ORDER.index(md.lord)
    total = md.end - md.start
    t = md.start
    res = []
    for k in range(9):
        l = VIMSHOTTARI_ORDER[(i + k) % 9]
        dur = total * VIMSHOTTARI_YEARS[l] / 120
        res.append(Dasha(l, t, t + dur))
        t += dur
    return res


def current_dasha(dashas: list[Dasha], jd: float) -> tuple[Dasha, Dasha | None]:
    for md in dashas:
        if md.start <= jd < md.end:
            for ad in md.sub or []:
                if ad.start <= jd < ad.end:
                    return md, ad
            return md, None
    raise ValueError("дата вне диапазона даш")


@dataclass
class Chart:
    birth: datetime
    loc: Location
    jd: float
    asc: float
    planets: dict[str, Body]
    dashas: list[Dasha]

    @property
    def lagna_rashi(self) -> int:
        return int(self.asc // 30)

    @property
    def moon_rashi(self) -> int:
        return self.planets["Mo"].rashi

    def summary(self) -> str:
        lines = [f"Рождение: {self.birth:%d.%m.%Y %H:%M} ({self.loc.name})",
                 f"Лагна: {RASHI[self.lagna_rashi]['ru']} {self.asc % 30:.1f}°",
                 f"Луна: {RASHI[self.moon_rashi]['ru']}, накшатра {NAKSHATRA[self.planets['Mo'].nakshatra]['ru']}"]
        for c, b in self.planets.items():
            h = (b.rashi - self.lagna_rashi) % 12 + 1
            lines.append(f"  {b.describe()} — {h}-й дом")
        return "\n".join(lines)


def build_chart(birth: datetime, loc: Location, s: Settings | None = None) -> Chart:
    s = s or Settings(location=loc)
    if birth.tzinfo is None:
        birth = birth.replace(tzinfo=loc.zone)
    jd = to_jd(birth)
    pos = positions(jd, s)
    return Chart(birth, loc, jd, lagna(jd, loc, s), pos, vimshottari(pos["Mo"].lon, jd))
