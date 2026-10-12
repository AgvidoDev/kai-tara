"""Поиск городов по названию (офлайн, данные GeoNames, CC BY 4.0).

data/cities.tsv.gz собирается скриптом tools/build_cities.py: Россия и СНГ от 1000 жителей,
мир от 15 000. Индекс строится в памяти при первом обращении.
"""
from __future__ import annotations

import bisect
import gzip
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "cities.tsv.gz"
CIS = {"RU", "UA", "BY", "KZ", "UZ", "KG", "TJ", "TM", "AZ", "AM", "GE", "MD"}


@dataclass(frozen=True)
class City:
    gid: str
    ru: str
    en: str
    cc: str
    region_en: str
    region_ru: str
    lat: float
    lon: float
    tz: str
    pop: int

    @property
    def key(self) -> str:
        """Ключ для users.city_key и callback-кнопок."""
        return f"gn{self.gid}"

    def label(self, lang: str = "ru") -> str:
        if lang == "en":
            return ", ".join(p for p in dict.fromkeys([self.en, self.region_en, self.cc]) if p)
        name, region = self.ru, self.region_ru
        parts = [name] + ([region] if region and region != name else [])
        if self.cc not in CIS:
            parts.append(self.cc)
        return ", ".join(parts)

    def name(self, lang: str = "ru") -> str:
        return self.en if lang == "en" else self.ru


def norm(s: str) -> str:
    s = s.lower().replace("ё", "е").replace("’", "'").strip()
    s = re.sub(r"\s*-\s*", "-", s)
    return re.sub(r"\s+", " ", s)


class _Index:
    def __init__(self, path: Path = DATA):
        self.cities: list[City] = []
        self.by_id: dict[str, City] = {}
        pairs: list[tuple[str, int]] = []
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                if line.startswith("#"):
                    continue
                gid, ru, en, cc, r_en, r_ru, lat, lon, tz, pop, keys = line.rstrip("\n").split("\t")
                c = City(gid, ru, en, cc, r_en, r_ru, float(lat), float(lon), tz, int(pop))
                i = len(self.cities)
                self.cities.append(c)
                self.by_id[gid] = c
                for k in keys.split("|"):
                    pairs.append((norm(k), i))
        pairs.sort()
        self.keys = [k for k, _ in pairs]
        self.idx = [i for _, i in pairs]

    def search(self, query: str, limit: int = 6) -> list[City]:
        q = norm(query)
        region = ""
        if "," in q:                       # «Октябрьский, Пермский» — уточнение региона
            q, region = (x.strip() for x in q.split(",", 1))
        if len(q) < 2:
            return []
        lo = bisect.bisect_left(self.keys, q)
        exact, prefix, seen = [], [], set()
        i = lo
        while i < len(self.keys) and self.keys[i].startswith(q):
            ci = self.idx[i]
            if ci not in seen:
                seen.add(ci)
                (exact if self.keys[i] == q else prefix).append(self.cities[ci])
            i += 1
        out = sorted(exact, key=lambda c: -c.pop) + sorted(prefix, key=lambda c: -c.pop)
        if region:
            out = [c for c in out if region in norm(c.region_ru) or region in norm(c.region_en)]
        return out[:limit]


@lru_cache(maxsize=1)
def index() -> _Index:
    return _Index()


def search(query: str, limit: int = 6) -> list[City]:
    return index().search(query, limit)


def by_key(key: str) -> City | None:
    """Город по ключу gn<geonameid>."""
    if not key.startswith("gn"):
        return None
    return index().by_id.get(key[2:])
