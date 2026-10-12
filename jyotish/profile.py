"""Астропрофиль: всё, что нужно сервису, без хранения даты, времени и места рождения.

Профиль считается один раз из данных рождения, после чего исходные данные можно забыть.
Это псевдонимизация, а не обезличивание: время и место рождения не восстановить, но знаки
медленных планет вместе с накшатрой Луны сужают дату рождения до 1–2 дней (проверено перебором).
Вместе с tg_id профиль остаётся персональными данными.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from .core import Location, Settings, body, from_jd, lagna, positions, to_jd, tropical_lon
from .natal import vimshottari

NAK_SPAN = 360 / 27
PLANET_ORDER = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]


@dataclass
class MoonPoint:
    """Луна для совместимости: знак, накшатра, пада и половина знака (для вашьи)."""
    rashi: int
    nakshatra: int
    pada: int                 # 1..4
    first_half: bool          # градус в знаке < 15

    @classmethod
    def from_lon(cls, lon: float) -> "MoonPoint":
        return cls(int(lon // 30), int(lon // NAK_SPAN), int((lon % NAK_SPAN) // (NAK_SPAN / 4)) + 1,
                   lon % 30 < 15)


@dataclass
class DashaSpan:
    lord: str
    start: str                # "YYYY-MM"
    end: str
    sub: list["DashaSpan"] = field(default_factory=list)


@dataclass
class AstroProfile:
    time_known: bool
    sun_trop_sign: int
    sun_sid_rashi: int
    moon_rashi: int | None                 # None — без времени Луна меняла знак в этот день
    moon_candidates: list[int]
    moon_nakshatra: int | None
    moon_pada: int | None
    moon_first_half: bool | None
    lagna_rashi: int | None
    planet_rashi: dict[str, int]
    dashas: list[DashaSpan] = field(default_factory=list)

    @property
    def moon(self) -> MoonPoint | None:
        if None in (self.moon_rashi, self.moon_nakshatra, self.moon_pada, self.moon_first_half):
            return None
        return MoonPoint(self.moon_rashi, self.moon_nakshatra, self.moon_pada, self.moon_first_half)

    def sign_for(self, mode: str) -> int | None:
        return {"moon": self.moon_rashi, "sun_sid": self.sun_sid_rashi, "sun_trop": self.sun_trop_sign}[mode]

    def current_dasha(self, now: datetime) -> tuple[DashaSpan | None, DashaSpan | None]:
        ym = f"{now:%Y-%m}"
        for md in self.dashas:
            if md.start <= ym < md.end:
                ad = next((a for a in md.sub if a.start <= ym < a.end), None)
                return md, ad
        return None, None

    def dashas_json(self) -> list[dict]:
        return [asdict(d) for d in self.dashas]

    @staticmethod
    def dashas_from_json(data: list[dict] | None) -> list[DashaSpan]:
        return [DashaSpan(d["lord"], d["start"], d["end"],
                          [DashaSpan(s["lord"], s["start"], s["end"]) for s in d.get("sub", [])])
                for d in (data or [])]


def _ym(jd: float, zone) -> str:
    return f"{from_jd(jd, zone):%Y-%m}"


def compute(birth: datetime, lat: float, lon: float, tz: str, time_known: bool,
            s: Settings | None = None) -> AstroProfile:
    s = s or Settings()
    zone = ZoneInfo(tz)
    birth = birth.replace(tzinfo=zone) if birth.tzinfo is None else birth
    if not time_known:
        birth = birth.replace(hour=12, minute=0)
    jd = to_jd(birth)
    pos = positions(jd, s)
    sun_trop = int(tropical_lon(jd, "Su") // 30)
    planet_rashi = {c: pos[c].rashi for c in PLANET_ORDER}
    if time_known:
        mo = pos["Mo"]
        mp = MoonPoint.from_lon(mo.lon)
        loc = Location("рождение", lat, lon, tz)
        dashas = [DashaSpan(md.lord, _ym(md.start, zone), _ym(md.end, zone),
                            [DashaSpan(ad.lord, _ym(ad.start, zone), _ym(ad.end, zone)) for ad in md.sub or []])
                  for md in vimshottari(mo.lon, jd)]
        return AstroProfile(True, sun_trop, pos["Su"].rashi, mo.rashi, [mo.rashi], mo.nakshatra, mp.pada,
                            mp.first_half, int(lagna(jd, loc, s) // 30), planet_rashi, dashas)
    m0 = body(to_jd(birth.replace(hour=0, minute=0)), "Mo", s)
    m1 = body(to_jd(birth.replace(hour=23, minute=59)), "Mo", s)
    if m0.rashi != m1.rashi:
        return AstroProfile(False, sun_trop, pos["Su"].rashi, None, [m0.rashi, m1.rashi], None, None, None,
                            None, planet_rashi)
    p0, p1 = MoonPoint.from_lon(m0.lon), MoonPoint.from_lon(m1.lon)
    nak = m0.nakshatra if m0.nakshatra == m1.nakshatra else None
    pada = p0.pada if nak is not None and p0.pada == p1.pada else None
    half = p0.first_half if p0.first_half == p1.first_half else None
    return AstroProfile(False, sun_trop, pos["Su"].rashi, m0.rashi, [m0.rashi], nak, pada, half, None,
                        planet_rashi)
