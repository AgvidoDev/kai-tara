"""Расчётное ядро: сидерические позиции планет (Swiss Ephemeris, айанамша Лахири)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import swisseph as swe

from .kb import RASHI, NAKSHATRA, PLANET_RU

# ---------------------------------------------------------------- настройки
AYANAMSHA = {
    "lahiri": swe.SIDM_LAHIRI,
    "raman": swe.SIDM_RAMAN,
    "krishnamurti": swe.SIDM_KRISHNAMURTI,
}

PLANETS = {  # порядок как в джйотиш
    "Su": swe.SUN, "Mo": swe.MOON, "Ma": swe.MARS, "Me": swe.MERCURY,
    "Ju": swe.JUPITER, "Ve": swe.VENUS, "Sa": swe.SATURN, "Ra": None, "Ke": None,
}


@dataclass
class Location:
    name: str
    lat: float
    lon: float
    tz: str

    @property
    def zone(self) -> ZoneInfo:
        return ZoneInfo(self.tz)


CITIES = {
    "moscow": Location("Москва", 55.7558, 37.6173, "Europe/Moscow"),
    "spb": Location("Санкт-Петербург", 59.9343, 30.3351, "Europe/Moscow"),
    "kyiv": Location("Киев", 50.4501, 30.5234, "Europe/Kyiv"),
    "minsk": Location("Минск", 53.9006, 27.5590, "Europe/Minsk"),
    "almaty": Location("Алматы", 43.2389, 76.8897, "Asia/Almaty"),
    "novosibirsk": Location("Новосибирск", 55.0084, 82.9357, "Asia/Novosibirsk"),
    "belgrade": Location("Белград", 44.7866, 20.4489, "Europe/Belgrade"),
    "tbilisi": Location("Тбилиси", 41.7151, 44.8271, "Asia/Tbilisi"),
    "london": Location("Лондон", 51.5072, -0.1276, "Europe/London"),
    "new_york": Location("Нью-Йорк", 40.7128, -74.0060, "America/New_York"),
    "los_angeles": Location("Лос-Анджелес", 34.0522, -118.2437, "America/Los_Angeles"),
    "toronto": Location("Торонто", 43.6532, -79.3832, "America/Toronto"),
    "sydney": Location("Сидней", -33.8688, 151.2093, "Australia/Sydney"),
    "dubai": Location("Дубай", 25.2048, 55.2708, "Asia/Dubai"),
    "berlin": Location("Берлин", 52.5200, 13.4050, "Europe/Berlin"),
    "paris": Location("Париж", 48.8566, 2.3522, "Europe/Paris"),
    "madrid": Location("Мадрид", 40.4168, -3.7038, "Europe/Madrid"),
    "rome": Location("Рим", 41.9028, 12.4964, "Europe/Rome"),
    "amsterdam": Location("Амстердам", 52.3676, 4.9041, "Europe/Amsterdam"),
    "singapore": Location("Сингапур", 1.3521, 103.8198, "Asia/Singapore"),
    "delhi": Location("Дели", 28.6139, 77.2090, "Asia/Kolkata"),
}
CITY_EN = {
    "moscow": "Moscow", "spb": "Saint Petersburg", "kyiv": "Kyiv", "minsk": "Minsk", "almaty": "Almaty",
    "novosibirsk": "Novosibirsk", "belgrade": "Belgrade", "tbilisi": "Tbilisi", "london": "London",
    "new_york": "New York", "los_angeles": "Los Angeles", "toronto": "Toronto", "sydney": "Sydney",
    "dubai": "Dubai", "berlin": "Berlin", "paris": "Paris", "madrid": "Madrid", "rome": "Rome",
    "amsterdam": "Amsterdam", "singapore": "Singapore", "delhi": "Delhi",
}
CITY_MENU = {   # какие города показывать кнопками на каждом языке
    "ru": ["moscow", "spb", "novosibirsk", "kyiv", "minsk", "almaty", "tbilisi", "belgrade"],
    "en": ["london", "new_york", "los_angeles", "toronto", "sydney", "dubai", "berlin", "paris",
           "madrid", "rome", "amsterdam", "singapore"],
}
DEFAULT_CITY = {"ru": "moscow", "en": "london"}


def city_name(key: str, lang: str = "ru") -> str:
    if key and key.startswith("gn"):
        from .geo import by_key
        c = by_key(key)
        return c.label(lang) if c else key
    if lang == "en":
        return CITY_EN.get(key, key)
    loc = CITIES.get(key)
    return loc.name if loc else key


def location_for(key: str) -> Location:
    """Location для ключа города: популярный (moscow) или найденный в GeoNames (gn<id>)."""
    if key and key.startswith("gn"):
        from .geo import by_key
        c = by_key(key)
        if c:
            return Location(c.ru, c.lat, c.lon, c.tz)
    return CITIES.get(key, CITIES["moscow"])
DEFAULT_LOCATION = CITIES["moscow"]


@dataclass
class Settings:
    ayanamsha: str = "lahiri"
    true_node: bool = False       # средний узел (как в индийских панчангах); True — истинный
    location: Location = field(default_factory=lambda: DEFAULT_LOCATION)

    def apply(self) -> None:
        swe.set_sid_mode(AYANAMSHA[self.ayanamsha])

    @property
    def flags(self) -> int:
        return swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED


# ---------------------------------------------------------------- время
def to_jd(dt: datetime) -> float:
    """datetime с таймзоной -> юлианский день UT."""
    if dt.tzinfo is None:
        raise ValueError("datetime без часового пояса")
    u = dt.astimezone(timezone.utc)
    return swe.julday(u.year, u.month, u.day, u.hour + u.minute / 60 + u.second / 3600)


def from_jd(jd: float, tz: ZoneInfo | str = "UTC") -> datetime:
    y, m, d, h = swe.revjul(jd)
    hh = int(h); mm = int((h - hh) * 60); ss = int(round(((h - hh) * 60 - mm) * 60))
    if ss == 60:
        ss = 59
    dt = datetime(y, m, d, hh, mm, ss, tzinfo=timezone.utc)
    return dt.astimezone(ZoneInfo(tz) if isinstance(tz, str) else tz)


# ---------------------------------------------------------------- позиции
@dataclass
class Body:
    code: str
    lon: float          # сидерическая долгота 0..360
    speed: float        # град/сутки

    @property
    def rashi(self) -> int:          # 0 = Меша (Овен)
        return int(self.lon // 30)

    @property
    def deg_in_sign(self) -> float:
        return self.lon % 30

    @property
    def nakshatra(self) -> int:      # 0 = Ашвини
        return int(self.lon // (360 / 27))

    @property
    def pada(self) -> int:
        return int((self.lon % (360 / 27)) // (360 / 108)) + 1

    @property
    def retro(self) -> bool:
        return self.speed < 0 and self.code not in ("Ra", "Ke")

    def describe(self) -> str:
        d = self.deg_in_sign
        r = " (R)" if self.retro else ""
        return (f"{PLANET_RU[self.code]}: {RASHI[self.rashi]['ru']} {int(d)}°{int((d % 1) * 60):02d}'"
                f"{r}, накшатра {NAKSHATRA[self.nakshatra]['ru']} ({self.pada} пада)")


def body(jd: float, code: str, s: Settings) -> Body:
    s.apply()
    if code in ("Ra", "Ke"):
        node = swe.TRUE_NODE if s.true_node else swe.MEAN_NODE
        xx, _ = swe.calc_ut(jd, node, s.flags)
        lon = xx[0] if code == "Ra" else (xx[0] + 180) % 360
        return Body(code, lon, xx[3])
    xx, _ = swe.calc_ut(jd, PLANETS[code], s.flags)
    return Body(code, xx[0], xx[3])


def positions(jd: float, s: Settings | None = None) -> dict[str, Body]:
    s = s or Settings()
    return {c: body(jd, c, s) for c in PLANETS}


def tropical_lon(jd: float, code: str) -> float:
    xx, _ = swe.calc_ut(jd, PLANETS[code], swe.FLG_SWIEPH)
    return xx[0]


def ayanamsha_value(jd: float, s: Settings | None = None) -> float:
    (s or Settings()).apply()
    return swe.get_ayanamsa_ut(jd)


def lagna(jd: float, loc: Location, s: Settings | None = None) -> float:
    """Сидерический асцендент."""
    s = s or Settings()
    s.apply()
    _, ascmc = swe.houses_ex(jd, loc.lat, loc.lon, b"W", swe.FLG_SIDEREAL)
    return ascmc[0]
