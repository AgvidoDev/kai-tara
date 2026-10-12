"""Анализ натальной карты для отчёта: достоинства планет, управители домов, йоги, даши.

Только расчёт и структура — тексты в report_texts.py (по языкам).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .compat import relation
from .core import from_jd, to_jd
from .kb import RASHI
from .natal import Chart, current_dasha

ORDER = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]
EXALT = {"Su": 0, "Mo": 1, "Ma": 9, "Me": 5, "Ju": 3, "Ve": 11, "Sa": 6}
OWN = {"Su": {4}, "Mo": {3}, "Ma": {0, 7}, "Me": {2, 5}, "Ju": {8, 11}, "Ve": {1, 6}, "Sa": {9, 10}}
KENDRA, TRIKONA, DUSTHANA = {1, 4, 7, 10}, {1, 5, 9}, {6, 8, 12}
MAHAPURUSHA = {"Ma": "ruchaka", "Me": "bhadra", "Ju": "hamsa", "Ve": "malavya", "Sa": "sasha"}


def dignity(code: str, rashi: int) -> str | None:
    """exalted | own | friend | neutral | enemy | debilitated; для Раху/Кету — None."""
    if code in ("Ra", "Ke"):
        return None
    if EXALT[code] == rashi:
        return "exalted"
    if (EXALT[code] + 6) % 12 == rashi:
        return "debilitated"
    if rashi in OWN[code]:
        return "own"
    lord = RASHI[rashi]["lord"]
    rel = relation(code, lord)
    return "friend" if rel > 0 else "enemy" if rel < 0 else "neutral"


@dataclass
class PlanetInfo:
    code: str
    rashi: int
    house: int
    lon: float
    nakshatra: int
    pada: int
    retro: bool
    dignity: str | None


@dataclass
class Yoga:
    code: str                      # gaja_kesari | budha_aditya | ... ; тексты в report_texts
    planets: list[str] = field(default_factory=list)
    extra: dict = field(default_factory=dict)


@dataclass
class DashaItem:
    lord: str
    start: datetime
    end: datetime
    current: bool = False


@dataclass
class ChartReport:
    time_known: bool
    lagna: int | None              # знак лагны (None без времени)
    ref: int                       # знак, от которого считаются дома (лагна или Луна)
    moon_rashi: int
    moon_nakshatra: int
    planets: list[PlanetInfo]
    house_lords: dict[int, tuple[str, int]]   # дом → (управитель, в каком доме стоит)
    yogas: list[Yoga]
    dashas: list[DashaItem]
    antardasha: DashaItem | None
    weak: list[str]                # планеты, которым полезны упаи

    def planet(self, code: str) -> PlanetInfo:
        return next(p for p in self.planets if p.code == code)


def _house(ref: int, rashi: int) -> int:
    return (rashi - ref) % 12 + 1


def analyze(ch: Chart, now: datetime, time_known: bool = True) -> ChartReport:
    ref = ch.lagna_rashi if time_known else ch.moon_rashi
    planets = [PlanetInfo(c, b.rashi, _house(ref, b.rashi), b.lon, b.nakshatra, b.pada, b.retro, dignity(c, b.rashi))
               for c, b in ((c, ch.planets[c]) for c in ORDER)]
    pos = {p.code: p for p in planets}
    lords = {}
    for h in range(1, 13):
        sign = (ref + h - 1) % 12
        lord = RASHI[sign]["lord"]
        lords[h] = (lord, pos[lord].house)

    yogas: list[Yoga] = []
    moon, jup = pos["Mo"], pos["Ju"]
    if _house(moon.rashi, jup.rashi) in KENDRA:
        yogas.append(Yoga("gaja_kesari", ["Ju", "Mo"]))
    if pos["Su"].rashi == pos["Me"].rashi:
        yogas.append(Yoga("budha_aditya", ["Su", "Me"]))
    if moon.rashi == pos["Ma"].rashi:
        yogas.append(Yoga("chandra_mangala", ["Mo", "Ma"]))
    for code, name in MAHAPURUSHA.items():
        p = pos[code]
        if p.dignity in ("own", "exalted") and p.house in KENDRA and time_known:
            yogas.append(Yoga(name, [code]))
    # Раджа-йога: управители кендры и триконы в одном знаке (разные планеты)
    kendra_l = {lords[h][0] for h in KENDRA}
    trikona_l = {lords[h][0] for h in TRIKONA}
    seen = set()
    for a in kendra_l:
        for b in trikona_l:
            if a != b and pos[a].rashi == pos[b].rashi and frozenset((a, b)) not in seen:
                seen.add(frozenset((a, b)))
                yogas.append(Yoga("raja", [a, b]))
    # Дхана-йога: управители 2/11 с управителями 5/9
    for a in {lords[2][0], lords[11][0]}:
        for b in {lords[5][0], lords[9][0]}:
            if a != b and pos[a].rashi == pos[b].rashi and frozenset((a, b, "dh")) not in seen:
                seen.add(frozenset((a, b, "dh")))
                yogas.append(Yoga("dhana", [a, b]))
    # Випарита-раджа-йога: управитель дустханы в другой дустхане
    for h in DUSTHANA:
        lord, where = lords[h]
        if where in DUSTHANA and where != h:
            yogas.append(Yoga("vipareeta", [lord], {"house": h, "in": where}))
    # Мангала-доша
    if pos["Ma"].house in {1, 2, 4, 7, 8, 12}:
        yogas.append(Yoga("mangal_dosha", ["Ma"], {"house": pos["Ma"].house}))
    # Кемадрума: рядом с Луной (2-й и 12-й от неё, и в её знаке) нет планет, кроме Солнца и узлов
    near = {(moon.rashi + d) % 12 for d in (-1, 0, 1)}
    if not any(p.rashi in near for p in planets if p.code not in ("Mo", "Su", "Ra", "Ke")):
        yogas.append(Yoga("kemadruma", ["Mo"]))

    weak = [p.code for p in planets if p.dignity in ("debilitated", "enemy")]
    weak += [lords[h][0] for h in DUSTHANA if lords[h][0] not in weak and lords[h][1] in {1, 4, 7, 10}]

    dashas, ad_item = [], None
    if time_known:
        jd = to_jd(now)
        md, ad = current_dasha(ch.dashas, jd)
        zone = ch.loc.zone
        idx = next(i for i, d in enumerate(ch.dashas) if d is md)
        for d in ch.dashas[idx:idx + 4]:
            dashas.append(DashaItem(d.lord, from_jd(d.start, zone), from_jd(d.end, zone), d is md))
        if ad:
            ad_item = DashaItem(ad.lord, from_jd(ad.start, zone), from_jd(ad.end, zone), True)

    return ChartReport(time_known, ch.lagna_rashi if time_known else None, ref, moon.rashi, moon.nakshatra,
                       planets, lords, yogas, dashas, ad_item, weak[:4])
