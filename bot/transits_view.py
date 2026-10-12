"""Тексты больших транзитов для Telegram: по знаку (всем) и по натальной карте (Премиум)."""
from __future__ import annotations

from html import escape

from jyotish.gochara import tropical_to_sidereal_mix
from jyotish.profile import AstroProfile
from jyotish.texts import PLANET, SIGN, fmt_date, house_label, ordinal_en
from jyotish.transits import BODY, JUPITER, JUPITER_GOOD, KETU, RAHU, SATURN, SATURN_GOOD, BigTransit, house
from jyotish.transits_en import BODY_EN, JUPITER_EN, KETU_EN, RAHU_EN, SATURN_EN

from .astro_service import remedy_line

T = {
    "ru": {"body": BODY, "rahu": RAHU, "ketu": KETU, "jupiter": JUPITER, "saturn": SATURN},
    "en": {"body": BODY_EN, "rahu": RAHU_EN, "ketu": KETU_EN, "jupiter": JUPITER_EN, "saturn": SATURN_EN},
}
DISCLAIMER = {
    "ru": "<i>Прогноз носит ознакомительный характер и не заменяет консультацию врача.</i>",
    "en": "<i>This forecast is for information only and is not a substitute for medical advice.</i>",
}
HEALTH_NOTE = {
    "ru": "Режим сна, движение и плановые обследования — лучшая профилактика. Любые препараты и добавки — "
          "только после консультации врача.",
    "en": "Good sleep, exercise and routine check-ups are the best prevention. Any medicines or supplements — "
          "only after talking to a doctor.",
}

_LOC = ["в Овне", "в Тельце", "в Близнецах", "в Раке", "во Льве", "в Деве", "в Весах", "в Скорпионе",
        "в Стрельце", "в Козероге", "в Водолее", "в Рыбах"]          # где
_ACC = ["в Овен", "в Тельца", "в Близнецов", "в Рак", "во Льва", "в Деву", "в Весы", "в Скорпиона",
        "в Стрельца", "в Козерога", "в Водолея", "в Рыбы"]          # куда


def _cap(text: str) -> str:
    """Заглавная первая буква без str.capitalize(), которая опускает остальные («Раху» → «раху»)."""
    return text[:1].upper() + text[1:]


def _where(r: int, lang: str) -> str:
    return f"in {SIGN['en'][r]}" if lang == "en" else _LOC[r]


def _into(r: int, lang: str) -> str:
    return f"into {SIGN['en'][r]}" if lang == "en" else _ACC[r]


def _p(code: str, lang: str) -> str:
    return PLANET[lang][code]


def title(t: BigTransit, lang: str = "ru") -> str:
    if t.planet == "Ra":
        if lang == "en":
            return f"Nodal axis shift: Rahu {_where(t.rashi, lang)}, Ketu {_where(t.ketu_rashi, lang)}"
        return f"Смена оси узлов: Раху {_where(t.rashi, lang)}, Кету {_where(t.ketu_rashi, lang)}"
    return f"{_p(t.planet, lang)} {_where(t.rashi, lang)}"


def short_title(t: BigTransit, lang: str = "ru") -> str:
    S = SIGN[lang]
    if t.planet == "Ra":
        return f"🐉 {_p('Ra', lang)}/{_p('Ke', lang)}: {S[t.rashi]}–{S[t.ketu_rashi]}"
    icon = "⏳" if t.planet == "Sa" else "🪐"
    return f"{icon} {_p(t.planet, lang)} → {S[t.rashi]}"


def dates_line(t: BigTransit, lang: str = "ru") -> str:
    en = lang == "en"
    d = lambda x: fmt_date(x, lang)  # noqa: E731
    if t.planet == "Ra":
        if en:
            return (f"📅 From {d(t.start_true)} (true node) or {d(t.start)} (mean node) until "
                    f"{d(t.until)} (~1.5 years)")
        return (f"📅 С {d(t.start_true)} по истинному узлу или с {d(t.start)} по среднему — "
                f"до {d(t.until)} (~1,5 года)")
    line = f"📅 {'From' if en else 'С'} {d(t.start)} {'until' if en else 'до'} {d(t.until)}"
    for a, b in t.returns:
        who = _p(t.planet, lang)
        if en:
            line += (f"\n↩️ From {d(a)} to {d(b)} {who} goes retrograde back {_into(t.prev_rashi, lang)} — "
                     "last year's themes briefly return")
        else:
            line += (f"\n↩️ С {d(a)} по {d(b)} {who} ретроградно возвращается {_into(t.prev_rashi, lang)} — "
                     "темы прошлого года ненадолго вернутся")
    return line


def sign_for(mode: str, u, year: int, lang: str = "ru") -> tuple[int | None, str]:
    """Сидерический знак для массового прогноза и пояснение для режима «привычный знак»."""
    if mode == "moon":
        return u["moon_rashi"], ""
    if mode == "sun_sid":
        return u["sun_sid_rashi"], ""
    S = SIGN[lang]
    mix = tropical_to_sidereal_mix(u["sun_trop_sign"], year)
    main = mix[0][0]
    note = ""
    if len(mix) > 1 and mix[1][1] >= 0.15:
        w0, w1 = round(mix[0][1] * 100), round(mix[1][1] * 100)
        if lang == "en":
            note = (f"Your familiar sign {S[u['sun_trop_sign']]} is sidereal {S[main]} ({w0}%) or "
                    f"{S[mix[1][0]]} ({w1}%). If you were born near the boundary, read the forecast for "
                    f"{S[mix[1][0]]} as well.")
        else:
            note = (f"Ваш привычный знак {S[u['sun_trop_sign']]} по звёздам — это {S[main]} ({w0}%) или "
                    f"{S[mix[1][0]]} ({w1}%). Если родились на границе периода — прочитайте и прогноз для знака "
                    f"{S[mix[1][0]]}.")
    return main, note


def render_for_sign(t: BigTransit, sign: int, note: str = "", lang: str = "ru") -> str:
    en = lang == "en"
    out = [f"<b>{title(t, lang)}</b>", dates_line(t, lang), ""]
    out.append(f"♈ {'For' if en else 'Для знака'} <b>{SIGN[lang][sign]}</b> ({'sidereal' if en else 'сидерически'})")
    if note:
        out.append(f"<i>{escape(note)}</i>")
    out.append("")
    if t.planet == "Ra":
        out += _nodes_block(house(sign, t.rashi), house(sign, t.ketu_rashi), lang)
    elif t.planet == "Sa":
        out += _saturn_block(house(sign, t.rashi), lang)
    else:
        out += _jupiter_block(house(sign, t.rashi), lang)
    out += ["", DISCLAIMER[lang]]
    return "\n".join(out)


def _nodes_block(hr: int, hk: int, lang: str) -> list[str]:
    tx = T[lang]
    r, k = tx["rahu"][hr], tx["ketu"][hk]
    if lang == "en":
        return [
            f"Axis of the <b>{ordinal_en(hr)} and {ordinal_en(hk)} houses</b>.",
            f"🔺 Rahu in the {house_label('en', hr)} — where you're drawn and where you grow: {r['theme']}.",
            f"🔻 Ketu in the {house_label('en', hk)} — what to let go: {k['theme']}.",
            "",
            f"💰 <b>Money</b>\n• Opportunities: {r['money']}.\n• Limits: {k['money']}.",
            "",
            f"🩺 <b>Health</b>\nAreas to watch: {tx['body'][hr]}; {tx['body'][hk]}. {HEALTH_NOTE['en']}",
            "",
            f"💞 <b>Relationships</b>\n• Where to show up: {r['love']}.\n• What to let go: {k['love']}.",
            "",
            f"🧘 <b>Practice for the next 18 months</b>\n• {_cap(r['practice'])}.\n• {_cap(k['practice'])}.\n"
            "• Pick one small practice (15 minutes of meditation, early rising, a quiet day each week) and keep "
            "it for 40 days without a break — discipline is the best protection during a nodal shift.",
            "",
            "🪔 <b>Upayas</b>", remedy_line("Ra", "en"), remedy_line("Ke", "en"),
        ]
    return [
        f"Ось <b>{hr}-го и {hk}-го домов</b>.",
        f"🔺 Раху в {hr}-м доме — куда тянет и где рост: {r['theme']}.",
        f"🔻 Кету в {hk}-м доме — что отпустить: {k['theme']}.",
        "",
        f"💰 <b>Финансы</b>\n• Возможности: {r['money']}.\n• Ограничения: {k['money']}.",
        "",
        f"🩺 <b>Здоровье</b>\nВнимание к зонам: {tx['body'][hr]}; {tx['body'][hk]}. {HEALTH_NOTE['ru']}",
        "",
        f"💞 <b>Отношения</b>\n• Где проявиться: {r['love']}.\n• Где отпустить: {k['love']}.",
        "",
        f"🧘 <b>Практика на полтора года</b>\n• {_cap(r['practice'])}.\n• {_cap(k['practice'])}.\n"
        "• Выберите одну небольшую практику (медитация 15 минут, ранний подъём, день тишины в неделю) "
        "и держите её 40 дней без пропусков — дисциплина лучшая защита в период узлов.",
        "",
        "🪔 <b>Упаи</b>", remedy_line("Ra"), remedy_line("Ke"),
    ]


def _jupiter_block(h: int, lang: str) -> list[str]:
    good = h in JUPITER_GOOD
    txt = T[lang]["jupiter"][h]
    if lang == "en":
        return [f"Jupiter moves through your <b>{house_label('en', h)}</b>: {txt}.",
                ("✅ By the classical rules of gochara this is a favourable position — use it to grow." if good
                 else "ℹ️ Not the strongest position: growth comes through effort and conscious choice."),
                "", "🪔 <b>Upayas</b>", remedy_line("Ju", "en")]
    return [f"Юпитер идёт по вашему <b>{h}-му дому</b>: {txt}.",
            ("✅ По классическим правилам гочары это благоприятная позиция — используйте её для роста." if good
             else "ℹ️ Позиция не из самых сильных: рост придёт через усилия и осознанный выбор."),
            "", "🪔 <b>Упаи</b>", remedy_line("Ju")]


def _saturn_block(h: int, lang: str) -> list[str]:
    tx = T[lang]
    s = tx["saturn"][h]
    good = h in SATURN_GOOD
    if lang == "en":
        return [f"Saturn moves through your <b>{house_label('en', h)}</b>: {s['theme']}.",
                ("✅ By the classical rules of gochara this is a strong position for Saturn — hard work pays off."
                 if good else "ℹ️ A period that asks for patience: Saturn gives results slowly but surely."),
                "", f"💰 <b>Money</b>\n{_cap(s['money'])}.",
                "", f"🩺 <b>Health</b>\nAreas to watch: {tx['body'][h]}. {HEALTH_NOTE['en']}",
                "", f"💞 <b>Relationships</b>\n{_cap(s['love'])}.",
                "", f"🧘 <b>Practice</b>\n{_cap(s['practice'])}.",
                "", "🪔 <b>Upayas</b>", remedy_line("Sa", "en")]
    return [f"Сатурн идёт по вашему <b>{h}-му дому</b>: {s['theme']}.",
            ("✅ По классическим правилам гочары это сильная позиция Сатурна — труд окупится." if good
             else "ℹ️ Период требует терпения: Сатурн даёт результат медленно, но надёжно."),
            "", f"💰 <b>Финансы</b>\n{_cap(s['money'])}.",
            "", f"🩺 <b>Здоровье</b>\nВнимание к зонам: {tx['body'][h]}. {HEALTH_NOTE['ru']}",
            "", f"💞 <b>Отношения</b>\n{_cap(s['love'])}.",
            "", f"🧘 <b>Практика</b>\n{_cap(s['practice'])}.",
            "", "🪔 <b>Упаи</b>", remedy_line("Sa")]


def render_personal(t: BigTransit, p: AstroProfile, lang: str = "ru") -> str:
    """По натальной карте: дома от лагны и от Луны."""
    en = lang == "en"
    tx = T[lang]
    out = [f"🔮 <b>{title(t, lang)} — {'from your chart' if en else 'по вашей карте'}</b>", dates_line(t, lang), ""]
    refs = []
    if p.lagna_rashi is not None:
        refs.append(("From the Lagna" if en else "От лагны", p.lagna_rashi))
    if p.moon_rashi is not None:
        refs.append(("From the Moon" if en else "От Луны", p.moon_rashi))
    for name, ref in refs:
        if t.planet == "Ra":
            hr, hk = house(ref, t.rashi), house(ref, t.ketu_rashi)
            out += [f"<b>{name}</b>: {'axis' if en else 'ось'} {hr}/{hk}",
                    f"🔺 {_p('Ra', lang)} {'in the ' + house_label('en', hr) if en else f'в {hr}-м'}: {tx['rahu'][hr]['theme']}.",
                    f"🔻 {_p('Ke', lang)} {'in the ' + house_label('en', hk) if en else f'в {hk}-м'}: {tx['ketu'][hk]['theme']}.",
                    f"💰 {_cap(tx['rahu'][hr]['money'])}.",
                    f"💞 {_cap(tx['rahu'][hr]['love'])}.", ""]
        elif t.planet == "Sa":
            h = house(ref, t.rashi)
            where = f"in the {house_label('en', h)}" if en else f"в {h}-м доме"
            out += [f"<b>{name}</b>: {_p('Sa', lang)} {where} — {tx['saturn'][h]['theme']}.",
                    f"💰 {_cap(tx['saturn'][h]['money'])}.", ""]
        else:
            h = house(ref, t.rashi)
            where = f"in the {house_label('en', h)}" if en else f"в {h}-м доме"
            out += [f"<b>{name}</b>: {_p('Ju', lang)} {where} — {tx['jupiter'][h]}.", ""]
    if not refs:
        out.append("The personal version needs your birth time. ⚙️ Settings → Change birth data." if en else
                   "Для личной версии нужно время рождения. ⚙️ Настройки → Изменить данные рождения.")
    if t.planet == "Ra" and p.planet_rashi:
        conj = [c for c in ("Su", "Mo", "Ju", "Ve", "Sa") if p.planet_rashi.get(c) in (t.rashi, t.ketu_rashi)]
        if conj:
            names = ", ".join(_p(c, lang) for c in conj)
            out.append(f"⚡ The nodes pass through the signs of your natal {names} — you will feel this shift "
                       "more than most." if en else
                       f"⚡ Узлы проходят по знакам ваших натальных планет: {names} — для вас смена оси будет "
                       "ощутимее, чем для большинства.")
            out.append("")
    out.append(DISCLAIMER[lang])
    return "\n".join(out)


def teaser(t: BigTransit, days: int, lang: str = "ru") -> str:
    if lang == "en":
        when = "in a week" if days >= 5 else "very soon" if days > 0 else "today"
        if t.planet == "Ra":
            what = (f"🐉 <b>The nodal axis shifts {when}</b>: Rahu moves {_into(t.rashi, lang)}, Ketu "
                    f"{_into(t.ketu_rashi, lang)}. This is the main karmic background for all signs for 18 months.")
        elif t.planet == "Sa":
            what = (f"⏳ <b>Saturn moves {_into(t.rashi, lang)} {when}</b> — the planet of time and responsibility "
                    "changes sign for two and a half years. For some, Sade Sati begins; for others, it ends.")
        else:
            what = (f"🪐 <b>Jupiter moves {_into(t.rashi, lang)} {when}</b> — the planet of growth and luck changes "
                    "sign for almost a year.")
        return what + "\n\nWhat it means for you — tap the button below."
    when = "через неделю" if days >= 5 else "уже скоро" if days > 0 else "сегодня"
    if t.planet == "Ra":
        what = (f"🐉 <b>Смена оси узлов {when}</b>: Раху переходит {_into(t.rashi, lang)}, Кету — "
                f"{_into(t.ketu_rashi, lang)}. Это главный кармический фон на полтора года для всех знаков.")
    elif t.planet == "Sa":
        what = (f"⏳ <b>Сатурн {when} входит {_into(t.rashi, lang)}</b> — планета времени и ответственности меняет "
                "знак на два с половиной года. Для кого-то начнётся Саде-Сати, для кого-то закончится.")
    else:
        what = (f"🪐 <b>Юпитер {when} входит {_into(t.rashi, lang)}</b> — планета роста и удачи меняет знак "
                "почти на год.")
    return what + "\n\nЧто это значит именно для вас — нажмите кнопку ниже."
