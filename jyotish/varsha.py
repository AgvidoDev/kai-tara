"""Варшапхала (годовой прогноз, таджика): соляр, лагна года, мунтха, мудда-даша, смены знаков за год.

Базовый уровень: без сахам, таджика-йог и выбора управителя года из пяти кандидатов.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .core import Settings, body, from_jd, lagna, positions, to_jd
from .natal import Chart

SIDEREAL_YEAR = 365.256363
NAK = 360 / 27
# мудда-даша: порядок Вимшоттари, начиная с Солнца; длительность — доля от 120 «лет» Вимшоттари
MUDDA_ORDER = ["Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me", "Ke", "Ve"]
VIMSHOTTARI_YEARS = {"Su": 6, "Mo": 10, "Ma": 7, "Ra": 18, "Ju": 16, "Sa": 19, "Me": 17, "Ke": 7, "Ve": 20}
SLOW = ("Ju", "Sa", "Ra")
GOOD_MUNTHA = {9, 10, 11}
OK_MUNTHA = {1, 2, 3, 5}


@dataclass
class MuddaPeriod:
    lord: str
    start: datetime
    end: datetime


@dataclass
class Ingress:
    when: datetime
    code: str
    rashi: int
    retro: bool = False                   # возврат в прошлый знак попятным движением


@dataclass
class Varsha:
    age: int                              # полных лет на начало года
    start: datetime                       # момент соляра
    end: datetime                         # следующий соляр
    time_known: bool
    asc: float | None                     # лагна года (None без времени рождения)
    ref: int                              # знак, от которого считаются дома года
    planets: dict                         # code -> Body в момент соляра
    muntha: int                           # знак мунтхи
    mudda: list[MuddaPeriod] = field(default_factory=list)
    ingresses: list[Ingress] = field(default_factory=list)

    @property
    def lagna_rashi(self) -> int | None:
        return None if self.asc is None else int(self.asc // 30)

    def house(self, rashi: int) -> int:
        return (rashi - self.ref) % 12 + 1

    @property
    def muntha_house(self) -> int:
        return self.house(self.muntha)

    @property
    def muntha_quality(self) -> str:
        h = self.muntha_house
        return "good" if h in GOOD_MUNTHA else "ok" if h in OK_MUNTHA else "hard"

    def current_mudda(self, now: datetime) -> MuddaPeriod | None:
        return next((p for p in self.mudda if p.start <= now < p.end), None)


def solar_return(natal_sun: float, guess_jd: float, s: Settings) -> float:
    """Момент, когда сидерическое Солнце возвращается в натальную долготу (ближайший к guess_jd)."""
    jd = guess_jd
    for _ in range(8):
        sun = body(jd, "Su", s)
        diff = (natal_sun - sun.lon + 180) % 360 - 180
        jd += diff / sun.speed
        if abs(diff) < 1e-7:
            break
    return jd


def _sr(ch: Chart, age: int, s: Settings) -> float:
    return solar_return(ch.planets["Su"].lon, ch.jd + age * SIDEREAL_YEAR, s)


def year_age(ch: Chart, now: datetime, s: Settings) -> int:
    """Полных лет: номер соляра, в чьём году лежит now."""
    jd_now = to_jd(now)
    age = max(0, now.year - ch.birth.year)
    while age > 0 and _sr(ch, age, s) > jd_now:
        age -= 1
    while _sr(ch, age + 1, s) <= jd_now:
        age += 1
    return age


def mudda_dasha(moon_lon: float, age: int, start: datetime, end: datetime) -> list[MuddaPeriod]:
    """Мудда-даша: стартовый управитель = (номер накшатры + полных лет − 2) mod 9 от Солнца;
    первый период — остаток, как в натальной Вимшоттари, пройденная часть добавляется в конец года."""
    nak1 = int(moon_lon // NAK) + 1
    i0 = (nak1 + age - 3) % 9
    rest = 1 - (moon_lon % NAK) / NAK
    total = (end - start).total_seconds()
    parts: list[tuple[str, float]] = []
    first = MUDDA_ORDER[i0]
    parts.append((first, VIMSHOTTARI_YEARS[first] / 120 * rest))
    for k in range(1, 9):
        lord = MUDDA_ORDER[(i0 + k) % 9]
        parts.append((lord, VIMSHOTTARI_YEARS[lord] / 120))
    if rest < 1:
        parts.append((first, VIMSHOTTARI_YEARS[first] / 120 * (1 - rest)))
    out, t = [], start
    for lord, frac in parts:
        nxt = t + timedelta(seconds=total * frac)
        if nxt > t:
            out.append(MuddaPeriod(lord, t, nxt))
        t = nxt
    out[-1].end = end
    return out


def ingresses(jd0: float, jd1: float, s: Settings, zone) -> list[Ingress]:
    """Смены знака у Юпитера, Сатурна и Раху/Кету за год (шаг — сутки, точность до дня)."""
    out = []
    for code in SLOW:
        prev = body(jd0, code, s).rashi
        jd = jd0 + 1
        while jd <= jd1:
            b = body(jd, code, s)
            r = b.rashi
            if r != prev:
                out.append(Ingress(from_jd(jd, zone), code, r, b.retro))
                prev = r
            jd += 1
    out.sort(key=lambda x: x.when)
    return out


def build_varsha(ch: Chart, now: datetime, time_known: bool, s: Settings | None = None,
                 age: int | None = None) -> Varsha:
    s = s or Settings(location=ch.loc)
    zone = ch.loc.zone
    if age is None:
        age = year_age(ch, now, s)
    jd0, jd1 = _sr(ch, age, s), _sr(ch, age + 1, s)
    pos = positions(jd0, s)
    natal_ref = ch.lagna_rashi if time_known else ch.moon_rashi
    asc = lagna(jd0, ch.loc, s) if time_known else None
    ref = int(asc // 30) if asc is not None else natal_ref          # без времени — дома от натальной Луны
    start, end = from_jd(jd0, zone), from_jd(jd1, zone)
    return Varsha(age=age, start=start, end=end, time_known=time_known, asc=asc, ref=ref, planets=pos,
                  muntha=(natal_ref + age) % 12,
                  mudda=mudda_dasha(ch.planets["Mo"].lon, age, start, end),
                  ingresses=ingresses(jd0, jd1, s, zone))
