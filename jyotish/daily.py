"""Панчанга дня и личная оценка дня: накшатра, титхи, вара, тара-бала, чандра-бала.

Расчёт отдаёт коды и индексы; тексты на нужном языке — функции describe_sky/advice/reasons_text.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

import swisseph as swe

from .core import Location, Settings, body, from_jd, to_jd
from .events import _bisect, _elong
from .kb import NAKSHATRA
from .texts import (HOUSE, NAKSHATRA_NAME, NATURE, NATURE_DO, PAKSHA, PAKSHA_LONG, PLANET, SIGN, SPECIAL,
                    TARA as TARA_TEXT, TITHI_GROUP, TITHI_GROUP_MEANING, TONE, VARA, VARA_GOOD_FOR,
                    house_label, tithi_name)

NAK_SPAN = 360 / 27

# Баллы 9 тар: Джанма, Сампат, Випат, Кшема, Пратьяк, Садхана, Наидхана, Митра, Парама-митра
TARA_SCORE = [0, 1, -1, 1, -1, 2, -2, 1, 2]
CHANDRA_GOOD = {1, 3, 6, 7, 10, 11}
RIKTA = 3                                  # индекс группы титхи «Рикта»
# Python weekday(): 0 = понедельник
VARA_LORD = ["Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Su"]


@dataclass
class DayInfo:
    day: date
    location: str
    sunrise: datetime
    nakshatra: int                         # накшатра Луны на восходе
    nak_change: datetime | None            # когда Луна перейдёт в следующую (в пределах суток)
    moon_rashi: int
    tithi: int                             # 1..30 на восходе
    vara: int                              # 0 = понедельник

    @property
    def waxing(self) -> bool:
        return self.tithi <= 15

    @property
    def tithi_group_idx(self) -> int:      # 0 Нанда, 1 Бхадра, 2 Джая, 3 Рикта, 4 Пурна
        return (self.tithi - 1) % 15 % 5

    @property
    def is_rikta(self) -> bool:
        return self.tithi_group_idx == RIKTA

    @property
    def vara_lord(self) -> str:
        return VARA_LORD[self.vara]

    @property
    def nature(self) -> str:
        return NAKSHATRA[self.nakshatra]["nature"]

    @property
    def special(self) -> list[str]:
        """Коды особых дней: ekadashi | amavasya | purnima | pushya."""
        out = []
        if self.tithi in (11, 26):
            out.append("ekadashi")
        if self.tithi == 30:
            out.append("amavasya")
        if self.tithi == 15:
            out.append("purnima")
        if self.nakshatra == 7:
            out.append("pushya")
        return out


def sunrise(d: date, loc: Location) -> datetime:
    jd0 = to_jd(datetime.combine(d, time(0, 0), tzinfo=loc.zone))
    res, tret = swe.rise_trans(jd0, swe.SUN, swe.CALC_RISE | swe.BIT_DISC_CENTER, (loc.lon, loc.lat, 0))
    if res != 0:  # полярный день/ночь — берём 06:00
        return datetime.combine(d, time(6, 0), tzinfo=loc.zone)
    return from_jd(tret[0], loc.zone)


def day_info(d: date, s: Settings | None = None) -> DayInfo:
    s = s or Settings()
    loc = s.location
    sr = sunrise(d, loc)
    jd = to_jd(sr)
    mo = body(jd, "Mo", s)
    tithi = int(_elong(jd, s) // 12) + 1
    # переход накшатры в ближайшие 24 часа
    change = None
    nxt_boundary = (mo.nakshatra + 1) * NAK_SPAN
    lon_end = body(jd + 1, "Mo", s).lon
    lon_end_unwrapped = lon_end + (360 if lon_end < mo.lon else 0)
    if lon_end_unwrapped >= nxt_boundary:
        t = _bisect(lambda x: ((body(x, "Mo", s).lon - nxt_boundary + 180) % 360) - 180, jd, jd + 1)
        change = from_jd(t, loc.zone)
    return DayInfo(d, loc.name, sr, mo.nakshatra, change, mo.rashi, tithi, d.weekday())


# ------------------------------------------------------------------ личное
def tara_index(janma_nak: int, day_nak: int) -> int:
    return (day_nak - janma_nak) % 27 % 9


def chandra_house(natal_moon_rashi: int, moon_rashi: int) -> int:
    return (moon_rashi - natal_moon_rashi) % 12 + 1


@dataclass
class PersonalDay:
    info: DayInfo
    tara: int | None = None                # 0..8
    chandra: int | None = None             # дом транзитной Луны от натальной
    score: int = 0
    reasons: list[dict] = field(default_factory=list)

    @property
    def tone(self) -> str:
        """Код: good | bad | calm."""
        if self.score >= 2:
            return "good"
        if self.score <= -2:
            return "bad"
        return "calm"

    @property
    def icon(self) -> str:
        return {"good": "🟢", "bad": "🔴"}.get(self.tone, "🟡")

    def tone_text(self, lang: str) -> str:
        return TONE[lang][self.tone]


def personal_day(info: DayInfo, natal_moon_rashi: int | None, natal_nak: int | None) -> PersonalDay:
    p = PersonalDay(info)
    if natal_nak is not None:
        p.tara = tara_index(natal_nak, info.nakshatra)
        p.score += TARA_SCORE[p.tara]
        p.reasons.append({"code": "tara", "idx": p.tara})
    if natal_moon_rashi is not None:
        p.chandra = chandra_house(natal_moon_rashi, info.moon_rashi)
        good = p.chandra in CHANDRA_GOOD
        p.score += 1 if good else -1
        p.reasons.append({"code": "chandra", "house": p.chandra, "good": good})
    if info.tithi == 30:
        p.score -= 1
        p.reasons.append({"code": "amavasya"})
    elif info.is_rikta:
        p.score -= 1
        p.reasons.append({"code": "rikta", "tithi": info.tithi})
    return p


def reasons_text(p: PersonalDay, lang: str) -> list[str]:
    en = lang == "en"
    out = []
    for r in p.reasons:
        c = r["code"]
        if c == "tara":
            name, meaning = TARA_TEXT[lang][r["idx"]]
            out.append(f"Tara Bala: {name} ({meaning})" if en else f"Тара-бала: {name} ({meaning})")
        elif c == "chandra":
            h = r["house"]
            if en:
                out.append(f"Chandra Bala: the Moon is in your {house_label('en', h)} "
                           f"({'supportive' if r['good'] else 'weak'})")
            else:
                out.append(f"Чандра-бала: Луна в вашем {h}-м доме ({'поддерживает' if r['good'] else 'ослаблена'})")
        elif c == "amavasya":
            out.append("Amavasya — energy is at its lowest" if en else "Амавасья — энергия на нуле")
        elif c == "rikta":
            t = tithi_name(lang, r["tithi"])
            out.append(f"Tithi {t} — Rikta (empty), not for beginnings" if en
                       else f"Титхи {t} — пустота, не для начинаний")
    return out


def advice(p: PersonalDay, lang: str = "ru") -> tuple[list[str], list[str]]:
    """Что делать / чего избегать."""
    en = lang == "en"
    info = p.info
    do = [NATURE_DO[lang][info.nature], VARA_GOOD_FOR[lang][info.vara_lord]]
    avoid = []
    if p.chandra is not None:
        theme = HOUSE[lang][p.chandra]
        if p.chandra in CHANDRA_GOOD:
            do.append(f"lean on: {theme}" if en else f"опирайтесь на: {theme}")
        else:
            avoid.append(f"be careful with: {theme}" if en else f"осторожнее с темами: {theme}")
    if p.tara is not None and TARA_SCORE[p.tara] < 0:
        avoid.append("risky decisions and signing important papers" if en
                     else "рискованные решения и подписание важных бумаг")
    if info.is_rikta or info.tithi == 30:
        avoid.append("new beginnings and big purchases" if en else "новые начинания и крупные покупки")
    if info.nature in ("острая", "жестокая"):
        avoid.append("peaceful beginnings and dates" if en else "мирные начинания и свидания")
    return do, avoid


def describe_sky(info: DayInfo, lang: str = "ru") -> list[str]:
    en = lang == "en"
    nak = NAKSHATRA_NAME[lang][info.nakshatra]
    sign = SIGN[lang][info.moon_rashi]
    nature = NATURE[lang][info.nature]
    lines = [f"Moon in {nak} nakshatra ({sign}), nature — {nature}" if en
             else f"Луна в накшатре {nak} ({sign}), природа — {nature}"]
    if info.nak_change:
        nxt = NAKSHATRA_NAME[lang][(info.nakshatra + 1) % 27]
        hhmm = f"{info.nak_change:%H:%M}"
        today = info.nak_change.date() == info.day
        if en:
            lines.append(f"{'At' if today else 'Tomorrow at'} {hhmm} the Moon moves into {nxt}")
        else:
            lines.append(f"{'В' if today else 'Завтра в'} {hhmm} Луна перейдёт в накшатру {nxt}")
    paksha = PAKSHA[lang][0 if info.waxing else 1]
    g = info.tithi_group_idx
    if en:
        lines.append(f"Tithi: {paksha} {tithi_name('en', info.tithi)} ({info.tithi}), "
                     f"{TITHI_GROUP['en'][g]} group — {TITHI_GROUP_MEANING['en'][g]}")
        art = "the " if info.vara_lord in ("Su", "Mo") else ""
        lines.append(f"Vara: {VARA['en'][info.vara]}, day of {art}{PLANET['en'][info.vara_lord]}")
    else:
        lines.append(f"Титхи: {paksha} {tithi_name('ru', info.tithi)} ({info.tithi}-й), "
                     f"группа {TITHI_GROUP['ru'][g]} — {TITHI_GROUP_MEANING['ru'][g]}")
        lines.append(f"Вара: {VARA['ru'][info.vara]}, день планеты {PLANET['ru'][info.vara_lord]}")
    return lines


def special_text(info: DayInfo, lang: str = "ru") -> list[str]:
    return [SPECIAL[lang][c] for c in info.special]


def paksha_long(info: DayInfo, lang: str = "ru") -> str:
    return PAKSHA_LONG[lang][0 if info.waxing else 1]


def month_days(start: date, n: int, s: Settings | None = None) -> list[DayInfo]:
    return [day_info(start + timedelta(days=i), s) for i in range(n)]
