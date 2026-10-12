"""Генератор прогноза на лунацию (новолуние/полнолуние) для 12 знаков.

Выход: структурированный JSON (факты для LLM/озвучки) + черновой текст Markdown.
"""
from __future__ import annotations

import json

from .core import Settings, from_jd, positions
from .events import Event, all_events, lunations
from .gochara import SignReading, read_all
from .kb import NAKSHATRA, PLANET_RU
from .texts import HOUSE, LUNATION_ADVICE as TX_LUNATION_ADVICE, PLANET, SIGN, TONE, \
    event_text, factor_text, flag_text

LUNATION_ADVICE = TX_LUNATION_ADVICE["ru"]    # обратная совместимость

MODE_TITLE = {
    "moon": "Режим A — по знаку Луны (классический джйотиш)",
    "sun_sid": "Режим B — по сидерическому знаку Солнца",
    "sun_trop": "Режим C — по привычному знаку зодиака (западные даты)",
}


def tone(score: float, lo: float, hi: float) -> str:
    """Код тона: good | bad | mixed (абсолютный порог + ранг среди 12 знаков)."""
    if score >= max(hi, 1.0):
        return "good"
    if score <= min(lo, -1.0):
        return "bad"
    return "mixed"


def lunation_house(r: SignReading, lun_rashi: int) -> list[tuple[int, float]]:
    if r.mix:
        return [((lun_rashi - rr) % 12 + 1, w) for rr, w in r.mix]
    return [((lun_rashi - r.ref_rashi) % 12 + 1, 1.0)]


def build(lunation: Event, s: Settings | None = None, year: int = 2026) -> dict:
    s = s or Settings()
    tz = s.location.zone
    pos = positions(lunation.jd, s)
    nxt = [e for e in lunations(lunation.jd + 1, lunation.jd + 32, s) if e.kind == lunation.kind][0]
    events = [e for e in all_events(lunation.jd + 0.01, nxt.jd, s) if e.kind not in ("new_moon",)]
    moon = pos["Mo"]
    data = {
        "event": {
            "kind": lunation.kind,
            "time_local": from_jd(lunation.jd, tz).isoformat(),
            "location": s.location.name,
            "rashi": lunation.rashi,
            "nakshatra": moon.nakshatra,
            "period_until": from_jd(nxt.jd, tz).isoformat(),
            "ayanamsha": s.ayanamsha,
        },
        "sky": [b.describe() for b in pos.values()],
        "period_events": [{"time_local": from_jd(e.jd, tz).isoformat(), **e.as_dict()} for e in events],
        "modes": {},
    }
    for mode in ("moon", "sun_sid", "sun_trop"):
        readings = read_all(lunation.jd, mode, s, year)
        scores = sorted(r.score for r in readings)
        lo, hi = scores[3], scores[8]
        signs = []
        for r in readings:
            lh = lunation_house(r, lunation.rashi)
            signs.append({
                "label": r.label,
                "score": r.score,
                "tone": tone(r.score, lo, hi),
                "lunation_houses": lh,
                "flags": r.flags,
                "support": [f.as_dict() for f in r.top(3, True)],
                "challenges": [f.as_dict() for f in r.top(3, False)],
                "blocked": [(f.planet, f.blocked_by) for f in r.factors if f.blocked_by],
                "mix": [(rr, round(w, 2)) for rr, w in (r.mix or [])],
            })
        data["modes"][mode] = signs
    return data


def to_markdown(d: dict, lang: str = "ru") -> str:
    """Черновой текст (CLI). Пока только по-русски — для разметки и сверки."""
    ev = d["event"]
    kind = "Новолуние" if ev["kind"] == "new_moon" else "Полнолуние"
    nak = NAKSHATRA[ev["nakshatra"]]
    out = [f"# {kind} {ev['time_local'][:16].replace('T', ' ')} ({ev['location']})",
           "",
           f"{kind} в сидерическом знаке **{SIGN['ru'][ev['rashi']]}**, накшатра **{nak['ru']}** "
           f"(управитель — {PLANET_RU[nak['lord']]}, божество — {nak['deity']}). "
           f"Период действия — до {ev['period_until'][:10]}. Айанамша: {ev['ayanamsha']}.",
           "", "## Небо в момент лунации", ""]
    out += [f"- {x}" for x in d["sky"]]
    out += ["", "## События периода", ""]
    out += [f"- {e['time_local'][:16].replace('T', ' ')} — {event_text('ru', e)}" for e in d["period_events"]]
    for mode, signs in d["modes"].items():
        out += ["", f"## {MODE_TITLE[mode]}", ""]
        if mode == "sun_sid":
            out += ["Расчёт по знакам совпадает с режимом A — транзиты считаются от знака одинаково. "
                    "Разница только в том, какой знак пользователь считает своим: здесь — знак, где "
                    "стояло Солнце при рождении (сидерически). Бот определяет его по дате рождения.", ""]
            continue
        for sg in signs:
            out += [f"### {sg['label']} — {TONE['ru'][sg['tone']]} период (балл {sg['score']:+.1f})", ""]
            if sg["mix"]:
                out.append("Сидерически это: " + ", ".join(f"{SIGN['ru'][n]} {round(w * 100)}%" for n, w in sg["mix"]) + ".")
            for h, w in sg["lunation_houses"]:
                pref = f"[{round(w * 100)}%] " if len(sg["lunation_houses"]) > 1 else ""
                out.append(f"{pref}{kind} в **{h}-м доме** ({HOUSE['ru'][h]}): {LUNATION_ADVICE[h]}.")
            if sg["flags"]:
                out.append("Особые факторы: " + "; ".join(flag_text("ru", f) for f in sg["flags"]) + ".")
            if sg["support"]:
                out.append("Поддержка: " + "; ".join(factor_text("ru", f) for f in sg["support"]) + ".")
            if sg["challenges"]:
                out.append("Сложности: " + "; ".join(factor_text("ru", f) for f in sg["challenges"]) + ".")
            if sg["blocked"]:
                out.append("Ослабленные благоприятные транзиты (ведха): " +
                           ", ".join(f"{PLANET['ru'][a]} (помеха: {PLANET['ru'][b]})" for a, b in sg["blocked"]) + ".")
            out.append("")
    out += ["---", "_Прогноз носит развлекательно-ознакомительный характер и не является "
            "рекомендацией к принятию медицинских, финансовых или юридических решений._"]
    return "\n".join(out)


def dump(d: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
