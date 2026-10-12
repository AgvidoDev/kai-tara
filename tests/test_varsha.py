"""Варшапхала: соляр, мунтха, мудда-даша, PDF и сценарий в боте."""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from aiogram.methods import SendDocument

from bot.varsha import build_varsha_pdf, sections
from jyotish.core import Location, Settings, body, to_jd
from jyotish.natal import build_chart
from jyotish.varsha import VIMSHOTTARI_YEARS, build_varsha, mudda_dasha, year_age
from tests.conftest import cb, msg
from tests.test_bot_flow import U, register
from tests.test_report import _chart

MSK = ZoneInfo("Europe/Moscow")
LOC = Location("СПб", 59.93, 30.33, "Europe/Moscow")
CH = build_chart(datetime(1980, 5, 14, 6, 30, tzinfo=MSK), LOC)
NOW = datetime(2026, 10, 11, tzinfo=MSK)
S = Settings(location=LOC)


def test_solar_return_puts_sun_back_at_natal_point():
    v = build_varsha(CH, NOW, True, S)
    assert v.age == 46
    assert v.start.date().month == 5 and v.start.year == 2026 and v.start <= NOW < v.end
    assert abs(body(to_jd(v.start), "Su", S).lon - CH.planets["Su"].lon) < 1e-4
    assert 365 <= (v.end - v.start).days <= 366


def test_age_switches_on_solar_return():
    v = build_varsha(CH, NOW, True, S)
    assert year_age(CH, v.start - timedelta(minutes=5), S) == 45
    assert year_age(CH, v.start + timedelta(minutes=5), S) == 46


def test_muntha_moves_one_sign_per_year():
    v = build_varsha(CH, NOW, True, S)
    assert v.muntha == (CH.lagna_rashi + 46) % 12
    assert build_varsha(CH, NOW, True, S, age=47).muntha == (v.muntha + 1) % 12


def test_mudda_dasha_covers_the_year():
    start = datetime(2026, 1, 1, tzinfo=MSK)
    end = datetime(2027, 1, 1, tzinfo=MSK)
    md = mudda_dasha(0.0, 0, start, end)                 # начало Ашвини, 0 лет: Кету целиком, без хвоста
    assert [p.lord for p in md] == ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
    assert md[0].start == start and md[-1].end == end
    assert all(a.end == b.start for a, b in zip(md, md[1:]))
    days = (md[1].end - md[1].start).total_seconds() / 86400
    assert abs(days - 365 * VIMSHOTTARI_YEARS["Ve"] / 120) < 0.01
    half = mudda_dasha(360 / 27 / 2, 0, start, end)      # середина накшатры: Кету в начале и в конце
    assert half[0].lord == half[-1].lord == "Ke" and len(half) == 10


def test_without_birth_time_houses_from_moon():
    v = build_varsha(CH, NOW, False, S)
    assert v.asc is None and v.ref == CH.moon_rashi and v.muntha == (CH.moon_rashi + 46) % 12


@pytest.mark.parametrize("lang", ["ru", "en"])
@pytest.mark.parametrize("known", [True, False])
def test_sections_and_pdf(lang, known):
    v = build_varsha(CH, NOW, known, S)
    secs = sections(v, NOW, lang)
    text = " ".join(t for _, items in secs for _, t in items)
    assert "{" not in text and "}" not in text
    assert len(secs) == (8 if known else 7)
    pdf = build_varsha_pdf(v, NOW, lang, "СПб")
    assert pdf[:4] == b"%PDF" and len(pdf) > 5000


@pytest.mark.asyncio
async def test_varsha_from_chart(tg, repo):
    dp, bot, fake, cfg = tg
    await register(dp, bot)
    cfg.free_until = date(2099, 1, 1)
    await _chart(dp, bot)
    fake.calls.clear()
    await dp.feed_update(bot, cb(U, "varsha:get"))
    docs = fake.of(SendDocument)
    assert docs and docs[0].document.filename == "kai_tara_year.pdf"
    fake.calls.clear()
    await dp.feed_update(bot, cb(U, "rep:get"))                    # разбор карты всё ещё доступен
    assert fake.of(SendDocument)


@pytest.mark.asyncio
async def test_varsha_command_without_chart_asks_for_it(tg, repo):
    dp, bot, fake, cfg = tg
    await register(dp, bot)
    cfg.free_until = date(2099, 1, 1)
    fake.calls.clear()
    await dp.feed_update(bot, msg(U, "/varsha"))
    assert not fake.of(SendDocument) and "/chart" in fake.texts(U)[-1]
    await _chart(dp, bot)
    fake.calls.clear()
    await dp.feed_update(bot, msg(U, "/varsha"))
    assert fake.of(SendDocument)


def test_retrograde_return_is_marked():
    v = build_varsha(CH, NOW, True, S)
    ju = [i for i in v.ingresses if i.code == "Ju"]
    assert [i.retro for i in ju] == [False, False, True]
    text = " ".join(t for _, items in sections(v, NOW, "ru") for _, t in items)
    assert "Попятное движение" in text
