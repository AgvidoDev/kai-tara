"""Поиск событий: новолуния/полнолуния, затмения, ингрессии (смена знака), стоянки."""
from __future__ import annotations

from dataclasses import dataclass

import swisseph as swe

from .core import Settings, body
from .kb import RASHI, PLANET_RU, TITHI_RU


@dataclass
class Event:
    jd: float
    kind: str           # new_moon | full_moon | ingress | station_r | station_d | solar_eclipse | lunar_eclipse
    planet: str | None = None
    rashi: int | None = None
    detail: str = ""
    subtype: str = ""       # для затмений: total | annular | hybrid | partial | penumbral

    def as_dict(self) -> dict:
        return {"kind": self.kind, "planet": self.planet, "rashi": self.rashi, "subtype": self.subtype}


def _elong(jd: float, s: Settings) -> float:
    return (body(jd, "Mo", s).lon - body(jd, "Su", s).lon) % 360


def _bisect(f, a: float, b: float, tol: float = 1e-6) -> float:
    fa = f(a)
    for _ in range(80):
        m = (a + b) / 2
        fm = f(m)
        if (fa < 0) == (fm < 0):
            a, fa = m, fm
        else:
            b = m
        if b - a < tol:
            break
    return (a + b) / 2


def lunations(jd0: float, jd1: float, s: Settings | None = None) -> list[Event]:
    s = s or Settings()
    out: list[Event] = []
    step = 0.5
    jd = jd0
    prev = _elong(jd, s)
    while jd < jd1:
        nxt = _elong(jd + step, s)
        # новолуние: элонгация переходит через 0
        if prev > 300 and nxt < 60:
            t = _bisect(lambda x: ((_elong(x, s) + 180) % 360) - 180, jd, jd + step)
            out.append(Event(t, "new_moon", "Mo", body(t, "Mo", s).rashi))
        # полнолуние: через 180
        if prev < 180 <= nxt:
            t = _bisect(lambda x: _elong(x, s) - 180, jd, jd + step)
            out.append(Event(t, "full_moon", "Mo", body(t, "Mo", s).rashi))
        prev, jd = nxt, jd + step
    return out


def ingresses(jd0: float, jd1: float, codes=("Su", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"),
              s: Settings | None = None) -> list[Event]:
    s = s or Settings()
    out = []
    for c in codes:
        step = 0.25 if c == "Mo" else 1.0
        jd = jd0
        prev = body(jd, c, s).rashi
        while jd < jd1:
            cur = body(jd + step, c, s).rashi
            if cur != prev:
                def f(x, c=c, prev=prev):
                    return 1.0 if body(x, c, s).rashi != prev else -1.0
                t = _bisect(f, jd, jd + step)
                out.append(Event(t, "ingress", c, cur, f"{PLANET_RU[c]} → {RASHI[cur]['ru']}"))
            prev, jd = cur, jd + step
    return out


def stations(jd0: float, jd1: float, codes=("Ma", "Me", "Ju", "Ve", "Sa"),
             s: Settings | None = None) -> list[Event]:
    s = s or Settings()
    out = []
    for c in codes:
        jd = jd0
        prev = body(jd, c, s).speed
        while jd < jd1:
            cur = body(jd + 1, c, s).speed
            if (prev < 0) != (cur < 0):
                t = _bisect(lambda x, c=c: body(x, c, s).speed, jd, jd + 1)
                kind = "station_r" if cur < 0 else "station_d"
                b = body(t, c, s)
                txt = "ретроградный" if kind == "station_r" else "директный"
                out.append(Event(t, kind, c, b.rashi, f"{PLANET_RU[c]} {txt} в знаке {RASHI[b.rashi]['ru']}"))
            prev, jd = cur, jd + 1
    return out


def eclipses(jd0: float, jd1: float, s: Settings | None = None) -> list[Event]:
    s = s or Settings()
    out = []
    jd = jd0
    while True:
        ret, tret = swe.sol_eclipse_when_glob(jd, swe.FLG_SWIEPH, 0, False)
        if tret[0] > jd1:
            break
        sub = ("total" if ret & swe.ECL_TOTAL else "annular" if ret & swe.ECL_ANNULAR
               else "hybrid" if ret & swe.ECL_ANNULAR_TOTAL else "partial")
        out.append(Event(tret[0], "solar_eclipse", "Su", body(tret[0], "Su", s).rashi,
                         "Солнечное затмение", sub))
        jd = tret[0] + 10
    jd = jd0
    while True:
        ret, tret = swe.lun_eclipse_when(jd, swe.FLG_SWIEPH, 0, False)
        if tret[0] > jd1:
            break
        sub = ("total" if ret & swe.ECL_TOTAL else "penumbral" if ret & swe.ECL_PENUMBRAL
               else "partial")
        out.append(Event(tret[0], "lunar_eclipse", "Mo", body(tret[0], "Mo", s).rashi,
                         "Лунное затмение", sub))
        jd = tret[0] + 10
    return sorted(out, key=lambda e: e.jd)


def tithi(jd: float, s: Settings | None = None) -> str:
    s = s or Settings()
    n = int(_elong(jd, s) // 12)  # 0..29
    paksha = "Шукла" if n < 15 else "Кришна"
    k = n % 15
    name = "Пурнима" if n == 14 else "Амавасья" if n == 29 else TITHI_RU[k]
    return f"{paksha} {name} ({n + 1}-й титхи)"


def all_events(jd0: float, jd1: float, s: Settings | None = None) -> list[Event]:
    s = s or Settings()
    ev = lunations(jd0, jd1, s) + ingresses(jd0, jd1, s=s) + stations(jd0, jd1, s=s) + eclipses(jd0, jd1, s)
    return sorted(ev, key=lambda e: e.jd)
