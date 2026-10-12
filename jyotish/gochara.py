"""Гочара (транзиты) для 12 знаков в трёх режимах.

Режимы:
  A  moon      — от сидерического знака Луны (раши), классика джйотиш
  B  sun_sid   — от сидерического знака Солнца
  C  sun_trop  — привычный «западный» знак по дате рождения; пересчитывается в
                 сидерические знаки Солнца с весами по реальным датам года
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

from .core import Body, Settings, positions, to_jd, tropical_lon, body
from .kb import GOCHARA_GOOD, PLANET_WEIGHT, RASHI, VEDHA, VEDHA_EXEMPT


def house_from(ref_rashi: int, b: Body) -> int:
    return (b.rashi - ref_rashi) % 12 + 1


@dataclass
class Factor:
    planet: str
    house: int
    good: bool
    blocked_by: str | None
    weight: float
    mix_rashi: int | None = None      # режим C: из какого сидерического знака этот фактор
    mix_weight: float | None = None

    def as_dict(self) -> dict:
        return {"planet": self.planet, "house": self.house, "mix_rashi": self.mix_rashi,
                "mix_weight": self.mix_weight}

    @property
    def raw(self) -> float:
        if self.good:
            return 0.0 if self.blocked_by else self.weight
        return -self.weight

    @property
    def score(self) -> float:
        """Отклонение от среднего: 0 = типичный фон, >0 лучше обычного, <0 хуже."""
        g = len(GOCHARA_GOOD[self.planet])
        expected = self.weight * (2 * g - 12) / 12
        return self.raw - expected


@dataclass
class SignReading:
    mode: str
    label: str
    ref_rashi: int | None
    factors: list[Factor] = field(default_factory=list)
    flags: list[dict] = field(default_factory=list)   # {"code": ..., "house": ...}; тексты — texts.flag_text
    mix: list[tuple[int, float]] | None = None  # для режима C: [(раши, вес)]

    @property
    def score(self) -> float:
        return round(sum(f.score for f in self.factors), 2)

    def top(self, n: int = 3, good: bool = True) -> list[Factor]:
        fs = [f for f in self.factors if not f.blocked_by and (f.score > 0 if good else f.score < 0)]
        return sorted(fs, key=lambda f: abs(f.score), reverse=True)[:n]


def read_from(ref: int, pos: dict[str, Body], mode: str, label: str,
              skip_moon: bool = True) -> SignReading:
    houses = {c: house_from(ref, b) for c, b in pos.items()}
    r = SignReading(mode, label, ref)
    for c, h in houses.items():
        if skip_moon and c == "Mo":
            continue  # Луна меняет знак каждые 2,5 дня — в периодных прогнозах не учитываем
        good = h in GOCHARA_GOOD[c]
        blocked = None
        if good and c in VEDHA and h in VEDHA[c]:
            vh = VEDHA[c][h]
            for c2, h2 in houses.items():
                if c2 != c and h2 == vh and (c, c2) not in VEDHA_EXEMPT and c2 not in ("Ra", "Ke"):
                    blocked = c2
                    break
        r.factors.append(Factor(c, h, good, blocked, PLANET_WEIGHT[c]))
    sa = houses["Sa"]
    if sa in (12, 1, 2):
        r.flags.append({"code": "sade_sati", "house": sa})
    elif sa == 8:
        r.flags.append({"code": "ashtama_shani", "house": 8})
    elif sa == 4:
        r.flags.append({"code": "kantaka_shani", "house": 4})
    if houses["Ju"] in GOCHARA_GOOD["Ju"]:
        r.flags.append({"code": "jupiter_support", "house": houses["Ju"]})
    return r


# ------------------------------------------------------------- режим C
def tropical_to_sidereal_mix(trop_sign: int, year: int, s: Settings | None = None) -> list[tuple[int, float]]:
    """Для западного знака возвращает доли сидерических знаков Солнца по дням года."""
    s = s or Settings()
    counts: dict[int, int] = {}
    d = date(year, 1, 1)
    while d.year == year:
        jd = to_jd(datetime(d.year, d.month, d.day, 12, tzinfo=timezone.utc))
        if int(tropical_lon(jd, "Su") // 30) == trop_sign:
            r = body(jd, "Su", s).rashi
            counts[r] = counts.get(r, 0) + 1
        d += timedelta(days=1)
    total = sum(counts.values())
    return sorted(((r, n / total) for r, n in counts.items()), key=lambda x: -x[1])


def read_all(jd: float, mode: str = "moon", s: Settings | None = None, year: int | None = None) -> list[SignReading]:
    s = s or Settings()
    pos = positions(jd, s)
    out = []
    for i in range(12):
        name = RASHI[i]["ru"]
        if mode == "moon":
            out.append(read_from(i, pos, mode, f"Луна в знаке {name} ({RASHI[i]['skt']})"))
        elif mode == "sun_sid":
            out.append(read_from(i, pos, mode, f"Солнце в знаке {name} (сидерически)"))
        elif mode == "sun_trop":
            mix = tropical_to_sidereal_mix(i, year or 2026, s)
            parts = [read_from(r, pos, mode, "") for r, _ in mix]
            combo = SignReading(mode, f"{name} (по западным датам)", None, mix=mix)
            for (r, w), part in zip(mix, parts):
                for f in part.factors:
                    combo.factors.append(Factor(f.planet, f.house, f.good, f.blocked_by, f.weight * w, r, w))
                combo.flags += [{**fl, "mix_rashi": r, "mix_weight": w} for fl in part.flags]
            out.append(combo)
        else:
            raise ValueError(mode)
    return out
