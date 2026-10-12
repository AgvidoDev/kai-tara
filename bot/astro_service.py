"""Мост между расчётным ядром и ботом: профиль, тексты для Telegram на языке пользователя."""
from __future__ import annotations

from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

from jyotish.compat import CompatResult, describe_moon
from jyotish.core import Settings, body, city_name, location_for, positions, to_jd
from jyotish.daily import PersonalDay, advice, day_info, describe_sky, personal_day, reasons_text, special_text
from jyotish.events import Event, lunations
from jyotish.forecast import build
from jyotish.gochara import read_from
from jyotish.muhurta import CATEGORIES as CAL_CATEGORIES, Calendar, build_calendar
from jyotish.profile import AstroProfile, MoonPoint, compute
from jyotish.texts import (CAL_CATEGORY, HOUSE, KUTA_NAME, LUNATION_ADVICE, NAKSHATRA_NAME, PLANET, REMEDY,
                           SIGN, SIGN_SKT, SIGN_SKT_LATIN, TONE, VERDICT, WEEKDAY_SHORT, dosha_text, event_text,
                           factor_text, flag_text, fmt_date, fmt_dt, house_label, kuta_detail, transit_note)

MODE_NAMES = {
    "ru": {"moon": "по знаку Луны (джйотиш)", "sun_sid": "по сидерическому знаку Солнца",
           "sun_trop": "по привычному знаку зодиака"},
    "en": {"moon": "by Moon sign (Jyotish)", "sun_sid": "by sidereal Sun sign",
           "sun_trop": "by your familiar zodiac sign"},
}
DISCLAIMER = {"ru": "<i>Прогноз носит ознакомительный характер.</i>",
              "en": "<i>This forecast is for information only.</i>"}


def _cap(text: str) -> str:
    return text[:1].upper() + text[1:]


def compute_profile(birth: datetime, lat: float, lon: float, tz: str, time_known: bool,
                    s: Settings | None = None) -> AstroProfile:
    return compute(birth, lat, lon, tz, time_known, s)


def describe_profile(p: AstroProfile, lang: str = "ru") -> str:
    en = lang == "en"
    S = SIGN[lang]
    skt = SIGN_SKT_LATIN if en else SIGN_SKT
    lines = [f"{'Western sign' if en else 'Знак по западным датам'}: <b>{S[p.sun_trop_sign]}</b>",
             f"{'Sidereal Sun' if en else 'Сидерическое Солнце'}: <b>{S[p.sun_sid_rashi]}</b> ({skt[p.sun_sid_rashi]})"]
    if p.moon_rashi is not None:
        nak = ""
        if p.moon_nakshatra is not None:
            n = NAKSHATRA_NAME[lang][p.moon_nakshatra]
            nak = f", {n} nakshatra" if en else f", накшатра {n}"
        lines.append(f"{'Moon' if en else 'Луна'}: <b>{S[p.moon_rashi]}</b> ({skt[p.moon_rashi]}){nak}")
    else:
        c = (" or " if en else " или ").join(S[r] for r in p.moon_candidates)
        need = "birth time needed to tell" if en else "нужно время рождения, чтобы уточнить"
        lines.append(f"{'Moon' if en else 'Луна'}: {c + ' — ' if c else ''}{need}")
    if p.lagna_rashi is not None:
        lines.append(f"{'Lagna (Ascendant)' if en else 'Лагна (асцендент)'}: <b>{S[p.lagna_rashi]}</b>")
    return "\n".join(lines)


# ------------------------------------------------------------ лунации
def current_new_moon(now: datetime, s: Settings) -> Event:
    jd = to_jd(now)
    return [e for e in lunations(jd - 31, jd + 0.001, s) if e.kind == "new_moon"][-1]


def next_lunation(now: datetime, s: Settings) -> Event:
    jd = to_jd(now)
    return lunations(jd, jd + 20, s)[0]


_cache: dict[tuple, dict] = {}


def lunation_facts(lun: Event, s: Settings) -> dict:
    key = (round(lun.jd, 4), s.location.name, s.ayanamsha, s.true_node)
    if key not in _cache:
        year = int(datetime.now().year)
        _cache[key] = build(lun, s, year)
    return _cache[key]


def render_sign(facts: dict, mode: str, sign: int, lang: str = "ru", city_key: str | None = None) -> str:
    """Текст прогноза для одного знака в HTML-разметке Telegram."""
    en = lang == "en"
    ev = facts["event"]
    sg = facts["modes"][mode][sign]
    new = ev["kind"] == "new_moon"
    kind = ("New Moon" if new else "Full Moon") if en else ("Новолуние" if new else "Полнолуние")
    when = datetime.fromisoformat(ev["time_local"])
    until = datetime.fromisoformat(ev["period_until"])
    place = city_name(city_key, lang) if city_key else ev["location"]
    nak = NAKSHATRA_NAME[lang][ev["nakshatra"]]
    out = [f"{'🌑' if new else '🌕'} <b>{kind} {fmt_dt(when, lang)}</b> ({escape(place)})",
           (f"Lunation sign: {SIGN['en'][ev['rashi']]}, {nak} nakshatra" if en
            else f"Знак лунации: {SIGN['ru'][ev['rashi']]}, накшатра {nak}"),
           f"{'Period: until' if en else 'Период: до'} {fmt_date(until, lang)}",
           "",
           f"<b>{escape(SIGN[lang][sign])}</b> — {MODE_NAMES[lang][mode]}",
           f"{'Overall tone' if en else 'Общий фон'}: <b>{TONE[lang][sg['tone']]}</b>"]
    if sg["mix"]:
        out.append(f"<i>{'Sidereally' if en else 'Сидерически'}: " +
                   ", ".join(f"{SIGN[lang][n]} {round(w * 100)}%" for n, w in sg["mix"]) + "</i>")
    out.append("")
    for h, w in sg["lunation_houses"]:
        pref = f"({round(w * 100)}%) " if len(sg["lunation_houses"]) > 1 else ""
        adv = _cap(LUNATION_ADVICE[lang][h])
        if en:
            out.append(f"🎯 {pref}Focus of the month — {house_label('en', h)}, {HOUSE['en'][h]}. {adv}.")
        else:
            out.append(f"🎯 {pref}Фокус месяца — {h}-й дом, {HOUSE['ru'][h]}. {adv}.")
    if sg["flags"]:
        out += ["", "⚠️ " + "\n⚠️ ".join(escape(flag_text(lang, f)) for f in sg["flags"])]
    if sg["support"]:
        out += ["", f"✅ <b>{'Support' if en else 'Поддержка'}</b>"] + \
               [f"• {escape(factor_text(lang, x))}" for x in sg["support"]]
    if sg["challenges"]:
        out += ["", f"⛔ <b>{'Challenges' if en else 'Сложности'}</b>"] + \
               [f"• {escape(factor_text(lang, x))}" for x in sg["challenges"]]
    ev_lines = [f"• {fmt_date(datetime.fromisoformat(e['time_local']), lang, year=False)} — "
                f"{escape(event_text(lang, e))}" for e in facts["period_events"]]
    if ev_lines:
        out += ["", f"📅 <b>{'Key dates' if en else 'Даты периода'}</b>"] + ev_lines
    out += ["", DISCLAIMER[lang]]
    return "\n".join(out)


# ------------------------------------------------------------ персональное
def _span(d, lang: str) -> str:
    return f"{PLANET[lang][d.lord]}: {d.start[5:]}.{d.start[:4]} – {d.end[5:]}.{d.end[:4]}"


def personal_text(p: AstroProfile, now: datetime, s: Settings | None = None, lang: str = "ru") -> str:
    """Личный прогноз по профилю: даши (до месяца), транзиты от лагны и Луны, упаи."""
    en = lang == "en"
    s = s or Settings()
    md, ad = p.current_dasha(now)
    pos = positions(to_jd(now), s)
    S = SIGN[lang]
    nak = NAKSHATRA_NAME[lang][p.moon_nakshatra]
    out = [f"🔮 <b>{'Personal forecast' if en else 'Персональный прогноз'}</b>", "",
           (f"Lagna: <b>{S[p.lagna_rashi]}</b>, Moon: <b>{S[p.moon_rashi]}</b>, {nak} nakshatra" if en else
            f"Лагна: <b>{S[p.lagna_rashi]}</b>, Луна: <b>{S[p.moon_rashi]}</b>, накшатра {nak}"), ""]
    if md:
        out.append(f"⏳ {'Mahadasha' if en else 'Махадаша'}: <b>{_span(md, lang)}</b>")
    if ad:
        out.append(f"⏳ {'Antardasha' if en else 'Антардаша'}: <b>{_span(ad, lang)}</b>")
    refs = ((p.lagna_rashi, "from the Lagna" if en else "от Лагны"), (p.moon_rashi, "from the Moon" if en else "от Луны"))
    for ref, name in refs:
        r = read_from(ref, pos, "personal", name)
        out += ["", f"<b>{'Transits' if en else 'Транзиты'} {name}</b>"]
        out += [f"✅ {escape(transit_note(lang, f.planet, f.house))}" for f in r.top(2, True)]
        out += [f"⛔ {escape(transit_note(lang, f.planet, f.house))}" for f in r.top(2, False)]
        out += [f"⚠️ {escape(flag_text(lang, x))}" for x in r.flags]
    for d in (md, ad):
        if d:
            h = (p.planet_rashi[d.lord] - p.lagna_rashi) % 12 + 1
            if en:
                out.append(f"\n{PLANET['en'][d.lord]} in your chart is in the {house_label('en', h)}: {HOUSE['en'][h]}.")
            else:
                out.append(f"\n{PLANET['ru'][d.lord]} в карте — в {h}-м доме: {HOUSE['ru'][h]}.")
    focus = ([md.lord] if md else []) + ([ad.lord] if ad and (not md or ad.lord != md.lord) else [])
    sa_house = (pos["Sa"].rashi - p.moon_rashi) % 12 + 1
    if sa_house in (12, 1, 2, 4, 8) and "Sa" not in focus:
        focus.append("Sa")
    out += ["", f"🪔 <b>{'Upayas (remedies)' if en else 'Упаи (рекомендации)'}</b>"] + [remedy_line(x, lang) for x in focus]
    out += [("<i>Gemstones are chosen only from a full chart in a consultation.</i>" if en
             else "<i>Камни подбирают только по полной карте на консультации.</i>"), "", DISCLAIMER[lang]]
    return "\n".join(out)


def remedy_line(planet: str, lang: str = "ru") -> str:
    r = REMEDY[lang][planet]
    if lang == "en":
        return (f"• <b>{PLANET['en'][planet]}</b> ({r['day']}): mantra “{r['mantra']}”, colour — {r['color']}; "
                f"charity — {r['charity']}; practice — {r['practice']}")
    return (f"• <b>{PLANET['ru'][planet]}</b> ({r['day']}): мантра «{r['mantra']}», цвет — {r['color']}; "
            f"благотворительность — {r['charity']}; практика — {r['practice']}")


# ------------------------------------------------------------ день
def daily_personal(d, s: Settings, natal_moon_rashi: int | None, natal_nak: int | None) -> PersonalDay:
    return personal_day(day_info(d, s), natal_moon_rashi, natal_nak)


def render_daily(p: PersonalDay, full: bool, lang: str = "ru", city_key: str | None = None,
                 who: str | None = None) -> str:
    en = lang == "en"
    i = p.info
    place = city_name(city_key, lang) if city_key else i.location
    out = [f"☀️ <b>{'Today' if en else 'Сегодня'}, {fmt_date(i.day, lang)}</b> ({escape(place)})",
           f"{(escape(who) if who else 'Your day' if en else 'Ваш день')}: {p.icon} <b>{p.tone_text(lang)}</b>", ""]
    out += describe_sky(i, lang)
    out += [f"✨ {x}" for x in special_text(i, lang)]
    if not full:
        out += ["", ("💎 Premium adds your personal Tara Bala and Chandra Bala, what to do and what to avoid, "
                     "and a morning message." if en else
                     "💎 В Премиуме: личная тара-бала и чандра-бала, что делать и чего избегать, утренняя рассылка.")]
        return "\n".join(out + ["", DISCLAIMER[lang]])
    reasons = reasons_text(p, lang)
    if reasons:
        out += ["", f"<b>{'Your factors' if en else 'Ваши показатели'}</b>"] + [f"• {escape(r)}" for r in reasons]
    do, avoid = advice(p, lang)
    out += ["", f"✅ <b>{'Good for' if en else 'Хорошо для'}</b>"] + [f"• {escape(x)}" for x in do]
    if avoid:
        out += ["", f"⛔ <b>{'Better to avoid' if en else 'Лучше избегать'}</b>"] + [f"• {escape(x)}" for x in avoid]
    if p.tara is None:
        out += ["", ("<i>Tara Bala needs your exact Moon nakshatra — add your birth time.</i>" if en else
                     "<i>Для тара-балы нужна точная накшатра Луны — укажите время рождения.</i>")]
    out += ["", DISCLAIMER[lang]]
    return "\n".join(out)


# ------------------------------------------------------------ календарь
def calendar_for(start, s: Settings, natal_moon_rashi: int | None, natal_nak: int | None) -> Calendar:
    return build_calendar(start, 30, natal_moon_rashi, natal_nak, s)


def _day_label(p: PersonalDay, lang: str) -> str:
    return f"{fmt_date(p.info.day, lang, year=False)} ({WEEKDAY_SHORT[lang][p.info.vara]})"


def render_calendar(cal: Calendar, location: str, lang: str = "ru") -> str:
    en = lang == "en"
    first, last = cal.days[0].info.day, cal.days[-1].info.day
    title = "Favourable days" if en else "Благоприятные дни"
    out = [f"📅 <b>{title} {fmt_date(first, lang, False)} – {fmt_date(last, lang, False)}</b> ({escape(location)})", ""]
    for cat in CAL_CATEGORIES:
        days = cal.best.get(cat.key) or []
        out.append(f"<b>{CAL_CATEGORY[lang][cat.key]}</b>")
        out.append(", ".join(f"{_day_label(p, lang)} {p.icon}" for p in days) if days
                   else ("— no suitable days" if en else "— подходящих дней нет"))
        out.append("")
    if cal.avoid:
        out.append(f"⛔ <b>{'Avoid starting important things' if en else 'Важное лучше не начинать'}:</b> " +
                   ", ".join(_day_label(p, lang) for p in cal.avoid))
        out.append("")
    if en:
        out += ["🟢 especially favourable for you, 🟡 personally neutral.",
                "Based on the day's nakshatra and tithi, the weekday and your Tara Bala and Chandra Bala (muhurta)."]
    else:
        out += ["🟢 особенно благоприятно для вас, 🟡 нейтрально лично для вас.",
                "Расчёт учитывает накшатру и титхи дня, день недели и ваши тара-балу и чандра-балу (мухурта)."]
    out += ["", DISCLAIMER[lang]]
    return "\n".join(out)


# ------------------------------------------------------------ совместимость
def render_compat(r: CompatResult, moon_a: MoonPoint, moon_b: MoonPoint, a_name: str, b_name: str,
                  lang: str = "ru") -> str:
    en = lang == "en"
    out = [f"💞 <b>{'Ashta Kuta compatibility' if en else 'Совместимость по ашта-куте'}</b>", "",
           f"{escape(a_name)}: {describe_moon(moon_a, lang)}", f"{escape(b_name)}: {describe_moon(moon_b, lang)}", "",
           (f"Total: <b>{r.total:g} of 36</b> — {VERDICT['en'][r.verdict]}" if en else
            f"Итого: <b>{r.total:g} из 36</b> — {VERDICT['ru'][r.verdict]}"), ""]
    for k in r.kutas:
        bar = "🟢" if k.score >= k.max * 0.75 else "🟡" if k.score >= k.max * 0.4 else "🔴"
        out.append(f"{bar} <b>{KUTA_NAME[lang][k.code]}</b>: {k.score:g}/{k.max:g} — "
                   f"{escape(kuta_detail(lang, {'code': k.code, 'args': k.args}))}")
    if r.doshas:
        out += [""] + [f"⚠️ {escape(dosha_text(lang, d))}" for d in r.doshas]
    out += ["", ("18 points or more is considered acceptable. Ashta Kuta looks only at the Moon; a full couple "
                 "analysis includes both birth charts." if en else
                 "18 баллов и выше — союз считается допустимым. Ашта-кута смотрит только на Луну; "
                 "полный анализ пары включает натальные карты обоих."), "", DISCLAIMER[lang]]
    return "\n".join(out)


def moon_lon(birth: datetime, tz: str, time_known: bool, s: Settings | None = None) -> tuple[float, bool]:
    """Долгота Луны и флаг «накшатра надёжна» (без времени — Луна на полдень)."""
    s = s or Settings()
    zone = ZoneInfo(tz)
    b = birth.replace(tzinfo=zone)
    if not time_known:
        b = b.replace(hour=12, minute=0)
        n0 = body(to_jd(b.replace(hour=0, minute=0)), "Mo", s).nakshatra
        n1 = body(to_jd(b.replace(hour=23, minute=59)), "Mo", s).nakshatra
        return body(to_jd(b), "Mo", s).lon, n0 == n1
    return body(to_jd(b), "Mo", s).lon, True


def settings_for(city_key: str) -> Settings:
    return Settings(location=location_for(city_key))
