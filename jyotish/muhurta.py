"""Календарь благоприятных дней (упрощённая мухурта на уровне дней)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .core import Settings
from .daily import TARA_SCORE, DayInfo, PersonalDay, month_days, personal_day

# Накшатры по индексу (0 = Ашвини)
ASHVINI, ROHINI, MRIGASHIRA, PUNARVASU, PUSHYA, UPHALGUNI, HASTA, CHITRA, SVATI, ANURADHA, \
    UASHADHA, SHRAVANA, DHANISHTHA, SHATABHISHA, UBHADRA, REVATI = \
    0, 3, 4, 6, 7, 11, 12, 13, 14, 16, 20, 21, 22, 23, 25, 26
MO, TU, WE, TH, FR, SA, SU = range(7)


@dataclass
class Category:
    key: str                  # название — texts.CAL_CATEGORY[lang][key]
    naks: set[int]
    varas: set[int]


CATEGORIES = [
    Category("money",
             {ASHVINI, PUSHYA, HASTA, CHITRA, ANURADHA, SHRAVANA, DHANISHTHA, REVATI, PUNARVASU, SVATI},
             {MO, WE, TH, FR}),
    Category("start",
             {ROHINI, UPHALGUNI, UASHADHA, UBHADRA, ASHVINI, PUSHYA, HASTA, MRIGASHIRA, CHITRA, ANURADHA, REVATI},
             {MO, WE, TH, FR}),
    Category("travel",
             {ASHVINI, MRIGASHIRA, PUNARVASU, PUSHYA, HASTA, ANURADHA, SHRAVANA, DHANISHTHA, REVATI},
             {MO, WE, TH, FR}),
    Category("beauty",
             {ASHVINI, MRIGASHIRA, PUNARVASU, PUSHYA, HASTA, CHITRA, SVATI, SHRAVANA, DHANISHTHA,
              SHATABHISHA, REVATI},
             {MO, WE, FR}),
    Category("health",
             {ASHVINI, PUSHYA, HASTA, MRIGASHIRA, CHITRA, ANURADHA, REVATI, SHATABHISHA, PUNARVASU, SVATI, SHRAVANA},
             {SU, MO, WE, TH}),
    Category("love",
             {ROHINI, MRIGASHIRA, UPHALGUNI, HASTA, SVATI, ANURADHA, UASHADHA, UBHADRA, REVATI, CHITRA},
             {MO, WE, TH, FR}),
    Category("home",
             {ROHINI, UPHALGUNI, UASHADHA, UBHADRA, MRIGASHIRA, CHITRA, ANURADHA, REVATI},
             {MO, WE, TH, FR}),
]


@dataclass
class Calendar:
    days: list[PersonalDay]
    best: dict[str, list[PersonalDay]] = field(default_factory=dict)
    avoid: list[PersonalDay] = field(default_factory=list)


def day_blocked(info: DayInfo) -> bool:
    """Общие запреты для любых начинаний: Рикта-титхи и Амавасья."""
    return info.is_rikta or info.tithi == 30


def personal_ok(p: PersonalDay) -> bool:
    """Плохая тара (Випат, Пратьяк, Наидхана) исключает день; слабая чандра-бала только снижает балл."""
    return p.tara is None or TARA_SCORE[p.tara] >= 0


def fits(p: PersonalDay, cat: Category) -> bool:
    i = p.info
    return (i.nakshatra in cat.naks and i.vara in cat.varas and not day_blocked(i) and personal_ok(p)
            and p.score > -2)


def build_calendar(start: date, n: int, natal_moon_rashi: int | None, natal_nak: int | None,
                   s: Settings | None = None, top: int = 5) -> Calendar:
    days = [personal_day(i, natal_moon_rashi, natal_nak) for i in month_days(start, n, s)]
    cal = Calendar(days)
    for cat in CATEGORIES:
        good = [p for p in days if fits(p, cat)]
        good.sort(key=lambda p: (-p.score, p.info.day))
        cal.best[cat.key] = sorted(good[:top], key=lambda p: p.info.day)
    cal.avoid = [p for p in days if p.score <= -2 or p.info.tithi == 30]
    return cal

