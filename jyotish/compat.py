"""Совместимость по ашта-куте (8 кут, максимум 36 баллов) — по Луне двух людей.

Сторона «A» — мужчина, «B» — женщина (классическая система несимметрична в варне, вашье,
гане и таре). Для однополых пар бот считает пользователя стороной A.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .kb import RASHI
from .profile import MoonPoint

NAK_SPAN = 360 / 27

# 1. Варна по знаку Луны: 4 брахман (водные), 3 кшатрий (огненные), 2 вайшья (земные), 1 шудра (воздушные)
VARNA = [3, 2, 1, 4, 3, 2, 1, 4, 3, 2, 1, 4]
VARNA_RU = {4: "брахман", 3: "кшатрий", 2: "вайшья", 1: "шудра"}

# 2. Вашья: 0 четвероногие, 1 человек, 2 водные, 3 дикие, 4 насекомые
VASHYA_RU = ["четвероногие", "человек", "водные", "дикие", "насекомые"]
VASHYA_TABLE = [  # строка — A, столбец — B
    [2, 1, 1, 0.5, 1],
    [1, 2, 0.5, 0, 1],
    [1, 0.5, 2, 1, 1],
    [0.5, 0, 1, 2, 0],
    [1, 1, 1, 0, 2],
]


def vashya_group(m: "MoonPoint | float") -> int:
    m = _point(m)
    r = m.rashi
    if r in (0, 1):
        return 0
    if r in (2, 5, 6, 10):
        return 1
    if r in (3, 11):
        return 2
    if r == 4:
        return 3
    if r == 7:
        return 4
    if r == 8:                       # Стрелец: первая половина — человек, вторая — четвероногие
        return 1 if m.first_half else 0
    return 0 if m.first_half else 2  # Козерог: первая половина — четвероногие, вторая — водные


def _point(m: "MoonPoint | float") -> MoonPoint:
    return m if isinstance(m, MoonPoint) else MoonPoint.from_lon(m)


# 4. Йони: животное и пол по накшатре
ANIMALS = ["лошадь", "слон", "баран", "змея", "собака", "кошка", "крыса", "корова", "буйвол",
           "тигр", "олень", "обезьяна", "мангуст", "лев"]
NAK_YONI = [0, 1, 2, 3, 3, 4, 5, 2, 5, 6, 6, 7, 8, 9, 8, 9, 10, 10, 4, 11, 12, 11, 13, 0, 13, 7, 1]
YONI_TABLE = [
    [4, 2, 2, 3, 2, 2, 2, 1, 0, 1, 3, 3, 2, 1],
    [2, 4, 3, 3, 2, 2, 2, 2, 3, 1, 2, 3, 2, 0],
    [2, 3, 4, 2, 1, 2, 1, 3, 3, 1, 2, 0, 3, 1],
    [3, 3, 2, 4, 2, 1, 1, 1, 1, 2, 2, 2, 0, 2],
    [2, 2, 1, 2, 4, 2, 1, 2, 2, 1, 0, 2, 1, 1],
    [2, 2, 2, 1, 2, 4, 0, 2, 2, 1, 3, 3, 2, 1],
    [2, 2, 1, 1, 1, 0, 4, 2, 2, 2, 2, 2, 1, 2],
    [1, 2, 3, 1, 2, 2, 2, 4, 3, 0, 3, 2, 2, 1],
    [0, 3, 3, 1, 2, 2, 2, 3, 4, 1, 2, 2, 2, 1],
    [1, 1, 1, 2, 1, 1, 2, 0, 1, 4, 1, 1, 2, 1],
    [3, 2, 2, 2, 0, 3, 2, 3, 2, 1, 4, 2, 2, 1],
    [3, 3, 0, 2, 2, 3, 2, 2, 2, 1, 2, 4, 3, 2],
    [2, 2, 3, 0, 1, 2, 1, 2, 2, 2, 2, 3, 4, 2],
    [1, 0, 1, 2, 1, 1, 2, 1, 1, 1, 1, 2, 2, 4],
]

# 5. Граха-майтри: естественная дружба управителей знаков Луны
FRIENDS = {
    "Su": ({"Mo", "Ma", "Ju"}, {"Me"}, {"Ve", "Sa"}),
    "Mo": ({"Su", "Me"}, {"Ma", "Ju", "Ve", "Sa"}, set()),
    "Ma": ({"Su", "Mo", "Ju"}, {"Ve", "Sa"}, {"Me"}),
    "Me": ({"Su", "Ve"}, {"Ma", "Ju", "Sa"}, {"Mo"}),
    "Ju": ({"Su", "Mo", "Ma"}, {"Sa"}, {"Me", "Ve"}),
    "Ve": ({"Me", "Sa"}, {"Ma", "Ju"}, {"Su", "Mo"}),
    "Sa": ({"Me", "Ve"}, {"Ju"}, {"Su", "Mo", "Ma"}),
}


def relation(a: str, b: str) -> int:
    """+1 друг, 0 нейтрал, -1 враг (как a относится к b)."""
    f, n, e = FRIENDS[a]
    return 1 if b in f else -1 if b in e else 0


MAITRI_SCORE = {(1, 1): 5, (1, 0): 4, (0, 0): 3, (1, -1): 1, (0, -1): 0.5, (-1, -1): 0}

# 6. Гана: 0 дэва, 1 манушья, 2 ракшаса
GANA_RU = ["дэва (божественная)", "манушья (человеческая)", "ракшаса (демоническая)"]
NAK_GANA = [0, 1, 2, 1, 0, 1, 0, 0, 2, 2, 1, 1, 0, 2, 0, 2, 0, 2, 2, 1, 1, 0, 2, 2, 1, 1, 0]
GANA_TABLE = [[6, 6, 0], [5, 6, 0], [1, 0, 6]]

# 8. Нади: 0 ади (вата), 1 мадхья (питта), 2 антья (капха)
NADI_RU = ["Ади (вата)", "Мадхья (питта)", "Антья (капха)"]
_NADI_CYCLE = [0, 1, 2, 2, 1, 0]


def nadi(nak: int) -> int:
    return _NADI_CYCLE[nak % 6]


@dataclass
class Kuta:
    code: str                 # varna | vashya | tara | yoni | maitri | gana | bhakoot | nadi
    score: float
    max: float
    args: dict = field(default_factory=dict)   # индексы для текста (texts.kuta_detail)


@dataclass
class CompatResult:
    kutas: list[Kuta] = field(default_factory=list)
    doshas: list[dict] = field(default_factory=list)   # {"code": "nadi"|"bhakoot", "cancelled": bool, ...}

    @property
    def total(self) -> float:
        return sum(k.score for k in self.kutas)

    @property
    def verdict(self) -> str:
        """Код: weak | medium | good | excellent."""
        t = self.total
        if t < 18:
            return "weak"
        if t < 25:
            return "medium"
        if t < 33:
            return "good"
        return "excellent"


def _tara_ok(frm: int, to: int) -> bool:
    return ((to - frm) % 27 % 9 + 1) not in (3, 5, 7)


def compat(moon_a: "MoonPoint | float", moon_b: "MoonPoint | float") -> CompatResult:
    """Луна A (мужчина) и B (женщина): MoonPoint или сидерическая долгота."""
    moon_a, moon_b = _point(moon_a), _point(moon_b)
    ra, rb = moon_a.rashi, moon_b.rashi
    na, nb = moon_a.nakshatra, moon_b.nakshatra
    res = CompatResult()

    v = 1 if VARNA[ra] >= VARNA[rb] else 0
    res.kutas.append(Kuta("varna", v, 1, {"a": VARNA[ra], "b": VARNA[rb]}))

    ga, gb = vashya_group(moon_a), vashya_group(moon_b)
    res.kutas.append(Kuta("vashya", VASHYA_TABLE[ga][gb], 2, {"a": ga, "b": gb}))

    t = 1.5 * _tara_ok(nb, na) + 1.5 * _tara_ok(na, nb)
    res.kutas.append(Kuta("tara", t, 3))

    ya, yb = NAK_YONI[na], NAK_YONI[nb]
    res.kutas.append(Kuta("yoni", YONI_TABLE[ya][yb], 4, {"a": ya, "b": yb}))

    la, lb = RASHI[ra]["lord"], RASHI[rb]["lord"]
    if la == lb:
        m = 5
    else:
        pair = tuple(sorted((relation(la, lb), relation(lb, la)), reverse=True))
        m = MAITRI_SCORE[pair]
    res.kutas.append(Kuta("maitri", m, 5, {"a": la, "b": lb}))

    g = GANA_TABLE[NAK_GANA[na]][NAK_GANA[nb]]
    res.kutas.append(Kuta("gana", g, 6, {"a": NAK_GANA[na], "b": NAK_GANA[nb]}))

    d1 = (rb - ra) % 12 + 1
    d2 = (ra - rb) % 12 + 1
    bad_bhakoot = {d1, d2} in ({2, 12}, {5, 9}, {6, 8})
    bh = 0 if bad_bhakoot else 7
    res.kutas.append(Kuta("bhakoot", bh, 7, {"d1": d1, "d2": d2}))
    if bad_bhakoot:
        cancel = la == lb or (relation(la, lb) == 1 and relation(lb, la) == 1)
        res.doshas.append({"code": "bhakoot", "lo": min(d1, d2), "hi": max(d1, d2), "cancelled": cancel})

    same_nadi = nadi(na) == nadi(nb)
    res.kutas.append(Kuta("nadi", 0 if same_nadi else 8, 8, {"a": nadi(na), "b": nadi(nb)}))
    if same_nadi:
        exc = ra == rb and na != nb or na == nb and moon_a.pada != moon_b.pada
        res.doshas.append({"code": "nadi", "cancelled": bool(exc)})
    return res


def describe_moon(m: "MoonPoint | float", lang: str = "ru") -> str:
    from .texts import NAKSHATRA_NAME, SIGN
    m = _point(m)
    if lang == "en":
        return f"Moon in {SIGN['en'][m.rashi]}, {NAKSHATRA_NAME['en'][m.nakshatra]} nakshatra"
    return f"Луна — {SIGN['ru'][m.rashi]}, накшатра {NAKSHATRA_NAME['ru'][m.nakshatra]}"
