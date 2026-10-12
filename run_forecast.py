"""CLI: прогноз на ближайшую лунацию.

  python run_forecast.py                     # ближайшее новолуние, Москва
  python run_forecast.py --kind full_moon --city spb
  python run_forecast.py --from 2026-12-01 --ayanamsha raman --true-node
  python run_forecast.py --chart "1980-05-14 06:30" --city spb   # натальная карта + даша
"""
import argparse
from datetime import datetime

from jyotish.core import CITIES, Settings, from_jd, to_jd
from jyotish.events import lunations
from jyotish.forecast import build, dump, to_markdown
from jyotish.natal import build_chart, current_dasha


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--kind", default="new_moon", choices=["new_moon", "full_moon"])
    p.add_argument("--city", default="moscow", choices=list(CITIES))
    p.add_argument("--from", dest="start", default=None, help="YYYY-MM-DD, по умолчанию сейчас")
    p.add_argument("--ayanamsha", default="lahiri")
    p.add_argument("--true-node", action="store_true")
    p.add_argument("--chart", default=None, help="'YYYY-MM-DD HH:MM' — построить натальную карту")
    p.add_argument("--out", default="forecast")
    a = p.parse_args()

    s = Settings(ayanamsha=a.ayanamsha, true_node=a.true_node, location=CITIES[a.city])
    tz = s.location.zone

    if a.chart:
        ch = build_chart(datetime.strptime(a.chart, "%Y-%m-%d %H:%M").replace(tzinfo=tz), s.location, s)
        print(ch.summary())
        md, ad = current_dasha(ch.dashas, to_jd(datetime.now(tz)))
        print("Текущая даша:", md.label(tz), "/", ad.label(tz) if ad else "")
        return

    start = datetime.strptime(a.start, "%Y-%m-%d").replace(tzinfo=tz) if a.start else datetime.now(tz)
    jd0 = to_jd(start)
    lun = next(e for e in lunations(jd0, jd0 + 32, s) if e.kind == a.kind)
    print("Лунация:", from_jd(lun.jd, tz))
    d = build(lun, s, year=start.year)
    dump(d, f"{a.out}.json")
    with open(f"{a.out}.md", "w", encoding="utf-8") as f:
        f.write(to_markdown(d))
    print(f"Готово: {a.out}.json, {a.out}.md")


if __name__ == "__main__":
    main()
