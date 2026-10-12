"""Сборка data/cities.tsv.gz из выгрузки GeoNames (CC BY 4.0, https://www.geonames.org).

Запуск: python tools/build_cities.py <cities1000.txt> <admin1CodesASCII.txt> <папка alternatenames>
Русские названия городов и регионов СНГ — из alternatenames/<CC>.txt (язык ru, предпочтительные).
Берём Россию и СНГ целиком (от 1000 жителей) и города мира от 15 000 жителей.
"""
import csv
import gzip
import re
import sys
from pathlib import Path

CIS = {"RU", "UA", "BY", "KZ", "UZ", "KG", "TJ", "TM", "AZ", "AM", "GE", "MD"}
WORLD_MIN_POP = 15000
NON_RU_CYR = re.compile(r"[іїєґђћљњџјѓќѕўңәөүұқғһҳӣӯҷҙҡҫӑӗӳ]", re.I)   # буквы других кириллических языков
CYR = re.compile(r"^[А-Яа-яЁё\- ]+$")
ANY_CYR = re.compile(r"[Ѐ-ӿ]")
LAT = re.compile(r"^[A-Za-z\-' .]+$")
TR = dict(zip("абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
              ["a", "b", "v", "g", "d", "e", "e", "zh", "z", "i", "y", "k", "l", "m", "n", "o", "p", "r", "s", "t",
               "u", "f", "kh", "ts", "ch", "sh", "shch", "\"", "y", "'", "e", "yu", "ya"]))


def translit(s: str) -> str:
    return "".join(TR.get(c, c) for c in s.lower())


def ru_name(name: str, alts: list[str]) -> str:
    """Русское название: кириллический вариант, ближе всего совпадающий с латинскими написаниями."""
    from difflib import SequenceMatcher
    cyr = [a for a in alts if CYR.match(a) and not NON_RU_CYR.search(a)]
    if not cyr:
        return name
    lats = [x.lower() for x in [name] + alts if LAT.match(x)]

    def score(c: str) -> tuple:
        t = translit(c)
        best = max((SequenceMatcher(None, t, x).ratio() for x in lats), default=0)
        words = len(c.split())
        base_words = min((len(x.split()) for x in lats), default=1)
        return (round(best, 3), -abs(words - base_words), -len(c))
    return max(cyr, key=score)


def load_ru_names(alt_dir: str) -> dict[str, str]:
    """geonameid → русское название: предпочтительное, не сокращение, не разговорное, не историческое."""
    best: dict[str, tuple] = {}
    for f in Path(alt_dir).glob("*.txt"):
        if f.name == "readme.txt":
            continue
        for line in open(f, encoding="utf-8"):
            p = line.rstrip("\n").split("\t")
            if len(p) < 8 or p[2] != "ru" or p[6] == "1" or p[7] == "1":
                continue
            rank = (p[4] == "1", p[5] != "1", -len(p[3]))
            if p[1] not in best or rank > best[p[1]][0]:
                best[p[1]] = (rank, p[3])
    return {k: v[1] for k, v in best.items()}


def main(cities_path: str, admin_path: str, alt_dir: str | None = None, out: str = "data/cities.tsv.gz") -> None:
    ru_names = load_ru_names(alt_dir) if alt_dir else {}
    admin, admin_ru = {}, {}
    for line in open(admin_path, encoding="utf-8"):
        code, name, ascii_name, gid = line.rstrip("\n").split("\t")
        admin[code] = ascii_name
        if gid in ru_names:
            admin_ru[code] = ru_names[gid]
    rows = []
    with open(cities_path, encoding="utf-8") as f:
        for r in csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            gid, name, ascii_name, alts, lat, lon, fclass, fcode, cc, _, a1 = r[:11]
            pop, tz = int(r[14] or 0), r[17]
            if fclass != "P" or not tz:
                continue
            if cc not in CIS and pop < WORLD_MIN_POP:
                continue
            alts_l = [a for a in alts.split(",") if a] if alts else []
            ru = ru_names.get(gid) or (ru_name(name, alts_l) if cc in CIS else ascii_name or name)
            # ключи поиска: кириллические варианты + латиница (имя, ascii)
            keys = {ru, name, ascii_name} | {a for a in alts_l if ANY_CYR.search(a)}
            if pop >= 100000 or cc in CIS:
                keys |= {a for a in alts_l if LAT.match(a)}
            keys = {k.lower().replace("ё", "е") for k in keys if k}
            region_en = admin.get(f"{cc}.{a1}", "")
            region_ru = admin_ru.get(f"{cc}.{a1}", region_en)
            rows.append([gid, ru, ascii_name or name, cc, region_en, region_ru, f"{float(lat):.4f}",
                         f"{float(lon):.4f}", tz, str(pop), "|".join(sorted(keys))])
    rows.sort(key=lambda x: -int(x[9]))
    Path(out).parent.mkdir(exist_ok=True)
    with gzip.open(out, "wt", encoding="utf-8", newline="") as g:
        g.write("# GeoNames (CC BY 4.0) https://www.geonames.org — id\tru\ten\tcc\tregion\tlat\tlon\ttz\tpop\tkeys\n")
        for r in rows:
            g.write("\t".join(r) + "\n")
    print(len(rows), "cities ->", out, Path(out).stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main(*sys.argv[1:4])
