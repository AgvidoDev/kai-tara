"""«Почему так?» — раскрытие расчётных факторов прогноза (лунация и «Сегодня»)."""
from __future__ import annotations

from aiogram.types import InlineKeyboardButton

from jyotish.daily import CHANDRA_GOOD, TARA_SCORE, PersonalDay
from jyotish.gochara import SignReading
from jyotish.kb import GOCHARA_GOOD, VEDHA
from jyotish.texts import (NAKSHATRA_NAME, PLANET, SIGN, TARA, TITHI_GROUP, TITHI_GROUP_MEANING, TONE, house_label,
                           ordinal_en, tithi_name)

from .i18n import t


def why_button(kind: str, lang: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=t(lang, "kb_why"), callback_data=f"why:{kind}")


def _h(lang: str, h: int) -> str:
    return house_label(lang, h)


def _blocker_house(planet: str, house: int) -> int | None:
    return VEDHA.get(planet, {}).get(house)


def explain_lunation(r: SignReading, all_scores: list[float], lun_rashi: int, sign: int | None, lang: str) -> str:
    """Факторы гочары для знака: дом каждой планеты, правило, ведха, вклад в балл, итоговый тон."""
    en = lang == "en"
    P, S = PLANET[lang], SIGN[lang]
    scores = sorted(all_scores)
    lo, hi = scores[3], scores[8]
    out = [f"❓ <b>{'Why this forecast' if en else 'Почему такой прогноз'}</b>", ""]
    if en:
        out.append("Each planet is counted by house from your sign. By the classical rules of gochara (Phaladeepika) "
                   "a planet helps only in certain houses; slow planets weigh more. A helpful transit can be cancelled "
                   "by vedha — a planet in the paired house.")
    else:
        out.append("Каждая планета считается по дому от вашего знака. По классическим правилам гочары (Пхаладипика) "
                   "планета помогает только в определённых домах; медленные планеты весят больше. Благоприятный "
                   "транзит может отменить ведха — планета в парном доме.")
    groups: dict = {}
    for f in r.factors:
        groups.setdefault((f.mix_rashi, f.mix_weight), []).append(f)
    for (mix_r, mix_w), factors in groups.items():
        out.append("")
        if mix_r is not None:
            out.append(f"<b>{S[mix_r]} {'sid.' if en else 'сид.'} ({round(mix_w * 100)}%)</b>")
        for f in sorted(factors, key=lambda x: -abs(x.score)):
            good_houses = ", ".join(str(x) for x in sorted(GOCHARA_GOOD[f.planet]))
            where = _h(lang, f.house)
            if f.good and f.blocked_by:
                bh = _blocker_house(f.planet, f.house)
                vedha = (f"vedha: {P[f.blocked_by]} in the {ordinal_en(bh)}" if en
                         else f"ведха: {P[f.blocked_by]} в {bh}-м") if bh else P[f.blocked_by]
                mark, verdict = "⚪", (f"helpful, but blocked ({vedha})" if en else f"благоприятен, но заблокирован ({vedha})")
            elif f.good:
                mark, verdict = "✅", ("helpful" if en else "благоприятен")
            else:
                mark, verdict = "⛔", ("not helpful" if en else "неблагоприятен")
            rule = f"good in {good_houses}" if en else f"хорош в {good_houses}"
            out.append(f"{mark} {P[f.planet]} — {where}: {verdict} ({rule}) → {f.score:+.2f}")
    tone = TONE[lang][_tone(r.score, lo, hi)]
    out += ["", (f"Total: <b>{r.score:+.2f}</b> → <b>{tone}</b>. A score is the deviation from a typical month: "
                 f"0 is an ordinary background. “Favourable” needs at least +1 and a place among the best signs of "
                 f"this lunation, “challenging” at most −1 and a place among the weakest." if en else
                 f"Итого: <b>{r.score:+.2f}</b> → <b>{tone}</b>. Балл — отклонение от обычного месяца: 0 — привычный "
                 f"фон. «Благоприятный» — от +1 и среди лучших знаков этой лунации, «напряжённый» — от −1 и "
                 f"среди слабых.")]
    if sign is not None:
        lh = (lun_rashi - sign) % 12 + 1
        out.append(f"🎯 {'The lunation falls in your' if en else 'Лунация падает в ваш'} {_h(lang, lh)} "
                   f"({S[lun_rashi]}) — {'the focus of the month' if en else 'это фокус месяца'}.")
    return "\n".join(out)


def _tone(score: float, lo: float, hi: float) -> str:
    if score >= max(hi, 1.0):
        return "good"
    if score <= min(lo, -1.0):
        return "bad"
    return "mixed"


def explain_day(p: PersonalDay, natal_nak: int | None, natal_moon: int | None, lang: str) -> str:
    """Тара-бала, чандра-бала и титхи: откуда взялась оценка дня."""
    en = lang == "en"
    i = p.info
    N, S = NAKSHATRA_NAME[lang], SIGN[lang]
    out = [f"❓ <b>{'Why this day' if en else 'Почему такой день'}</b>", ""]
    if natal_nak is not None and p.tara is not None:
        k = (i.nakshatra - natal_nak) % 27 + 1
        name, meaning = TARA[lang][p.tara]
        sc = TARA_SCORE[p.tara]
        if en:
            out.append(f"⭐ <b>Tara Bala</b>: today's Moon is in {N[i.nakshatra]}, your birth nakshatra is "
                       f"{N[natal_nak]}. Counting from yours, it's the {ordinal_en(k)} nakshatra; the count repeats "
                       f"every 9, so it's tara {p.tara + 1} — {name} ({meaning}) → {sc:+d}.")
        else:
            out.append(f"⭐ <b>Тара-бала</b>: Луна дня в накшатре {N[i.nakshatra]}, ваша накшатра рождения — "
                       f"{N[natal_nak]}. От вашей это {k}-я накшатра; счёт повторяется каждые 9, значит тара "
                       f"№{p.tara + 1} — {name} ({meaning}) → {sc:+d}.")
    else:
        out.append("⭐ Tara Bala needs your exact birth nakshatra (add your birth time)." if en else
                   "⭐ Для тара-балы нужна точная накшатра рождения (укажите время рождения).")
    if natal_moon is not None and p.chandra is not None:
        good = p.chandra in CHANDRA_GOOD
        houses = ", ".join(str(x) for x in sorted(CHANDRA_GOOD))
        if en:
            out.append(f"🌙 <b>Chandra Bala</b>: the Moon is in {S[i.moon_rashi]}, your natal Moon in "
                       f"{S[natal_moon]} — that's your {_h(lang, p.chandra)}. Good houses: {houses} → "
                       f"{'+1' if good else '−1'}.")
        else:
            out.append(f"🌙 <b>Чандра-бала</b>: Луна в знаке {S[i.moon_rashi]}, ваша натальная Луна — "
                       f"{S[natal_moon]}, это ваш {p.chandra}-й дом. Благоприятны дома {houses} → "
                       f"{'+1' if good else '−1'}.")
    g = i.tithi_group_idx
    pen = i.is_rikta or i.tithi == 30
    if en:
        out.append(f"🌗 <b>Tithi</b>: {tithi_name('en', i.tithi)} ({i.tithi}), {TITHI_GROUP['en'][g]} group — "
                   f"{TITHI_GROUP_MEANING['en'][g]}" + (" → −1 (not for beginnings)" if pen else " → 0"))
    else:
        out.append(f"🌗 <b>Титхи</b>: {tithi_name('ru', i.tithi)} ({i.tithi}-й), группа {TITHI_GROUP['ru'][g]} — "
                   f"{TITHI_GROUP_MEANING['ru'][g]}" + (" → −1 (не для начинаний)" if pen else " → 0"))
    tone = p.tone_text(lang)
    out += ["", (f"Total: <b>{p.score:+d}</b> → <b>{tone}</b> (+2 and above — favourable, −2 and below — "
                 f"challenging, otherwise calm)." if en else
                 f"Итого: <b>{p.score:+d}</b> → <b>{tone}</b> (от +2 — благоприятный, от −2 — напряжённый, "
                 f"иначе спокойный).")]
    return "\n".join(out)


# ------------------------------------------------------------------ обработчики
from aiogram import F, Router  # noqa: E402
from aiogram.types import CallbackQuery, InlineKeyboardMarkup  # noqa: E402

router = Router()


@router.callback_query(F.data == "why:lun")
async def why_lunation(c: CallbackQuery, repo, lang: str):
    import asyncio
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from jyotish.gochara import read_all

    from .astro_service import current_new_moon, settings_for
    from .glossary import linkify, terms_button
    u = await repo.get_user(c.from_user.id)
    if not u or not u["has_birth"]:
        return await c.answer(t(lang, "need_birth"), show_alert=True)
    mode = u["sign_mode"]
    sign = {"moon": u["moon_rashi"], "sun_sid": u["sun_sid_rashi"], "sun_trop": u["sun_trop_sign"]}[mode]
    if sign is None:
        return await c.answer(t(lang, "moon_unknown_mode"), show_alert=True)
    s = settings_for(u["city_key"])
    now = datetime.now(ZoneInfo(u["tz"]))

    def work():
        lun = current_new_moon(now, s)
        readings = read_all(lun.jd, mode, s, now.year)
        sid = None if mode == "sun_trop" else sign
        return explain_lunation(readings[sign], [r.score for r in readings], lun.rashi, sid, lang)

    text = await asyncio.to_thread(work)
    await c.message.answer(linkify(text, lang=lang), reply_markup=InlineKeyboardMarkup(inline_keyboard=[[terms_button(lang)]]))
    await c.answer()


@router.callback_query(F.data == "why:day")
async def why_today(c: CallbackQuery, repo, cfg, lang: str):
    import asyncio
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from .astro_service import daily_personal, settings_for
    from .glossary import linkify, terms_button
    from .payments import is_premium, send_paywall
    u = await repo.get_user(c.from_user.id)
    if not u or not u["has_birth"]:
        return await c.answer(t(lang, "need_birth"), show_alert=True)
    if not is_premium(u, cfg):                 # личные показатели дня — Премиум (кнопку можно подделать)
        await send_paywall(c.message, cfg, t(lang, "feat_personal"), lang=lang)
        return await c.answer()
    d = datetime.now(ZoneInfo(u["tz"])).date()
    p = await asyncio.to_thread(daily_personal, d, settings_for(u["city_key"]), u["moon_rashi"], u["moon_nakshatra"])
    text = explain_day(p, u["moon_nakshatra"], u["moon_rashi"], lang)
    await c.message.answer(linkify(text, lang=lang), reply_markup=InlineKeyboardMarkup(inline_keyboard=[[terms_button(lang)]]))
    await c.answer()
