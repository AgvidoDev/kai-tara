"""Большие транзиты: даты, тексты, бот и пуши."""
import dataclasses
import re
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest
from aiogram.methods import SendMessage

from bot import transits_handlers as th
from bot.transits_view import render_for_sign, render_personal, sign_for
from jyotish.profile import compute
from jyotish.transits import JUPITER, KETU, RAHU, big_transits
from tests.conftest import cb, msg
from tests.test_bot_flow import U, register

MSK = ZoneInfo("Europe/Moscow")
TS = big_transits(datetime(2026, 10, 11, tzinfo=MSK))


def test_dates_match_ephemeris():
    nodes = next(t for t in TS if t.planet == "Ra")
    jup = next(t for t in TS if t.planet == "Ju")
    assert (nodes.rashi, nodes.ketu_rashi) == (9, 3)                  # Козерог / Рак
    assert nodes.start.date() == date(2026, 12, 5) and nodes.start_true.date() == date(2026, 11, 25)
    assert nodes.until.date() == date(2028, 6, 23)
    assert jup.rashi == 4 and jup.start.date() == date(2026, 10, 31)
    assert [(a.date(), b.date()) for a, b in jup.returns] == [(date(2027, 1, 24), date(2027, 6, 26))]


def test_house_texts_complete():
    for table in (RAHU, KETU):
        assert set(table) == set(range(1, 13))
        assert all({"theme", "money", "love", "practice"} <= set(v) for v in table.values())
    assert set(JUPITER) == set(range(1, 13))


@pytest.mark.parametrize("sign", range(12))
def test_render_every_sign(sign):
    for t in TS:
        txt = render_for_sign(t, sign)
        assert len(txt) < 4000 and "None" not in txt
        assert "врача" in txt                                     # без медицинских назначений
    nodes = next(t for t in TS if t.planet == "Ra")
    assert f"Ось <b>{(9 - sign) % 12 + 1}-го" in render_for_sign(nodes, sign)


def test_known_axes_from_video():
    nodes = next(t for t in TS if t.planet == "Ra")
    assert "Ось <b>9-го и 3-го" in render_for_sign(nodes, 1)        # Телец
    assert "Ось <b>5-го и 11-го" in render_for_sign(nodes, 5)       # Дева
    assert "Ось <b>1-го и 7-го" in render_for_sign(nodes, 9)        # Козерог


def test_sun_trop_note_mentions_second_sign():
    sign, note = sign_for("sun_trop", {"sun_trop_sign": 1, "moon_rashi": None, "sun_sid_rashi": 0}, 2026)
    assert sign == 0 and "Телец" in note


def test_personal_uses_lagna_and_moon():
    p = compute(datetime(1980, 5, 14, 6, 30), 59.93, 30.33, "Europe/Moscow", True)
    nodes = next(t for t in TS if t.planet == "Ra")
    txt = render_personal(nodes, p)
    assert "От лагны" in txt and "От Луны" in txt


def test_push_stage():
    nodes = next(t for t in TS if t.planet == "Ra")
    assert th.push_stage(nodes, date(2026, 11, 18)) == "teaser"     # за 7 дней до 25.11
    assert th.push_stage(nodes, date(2026, 11, 25)) == "day"
    assert th.push_stage(nodes, date(2026, 11, 27)) == "day"
    assert th.push_stage(nodes, date(2026, 11, 28)) is None
    assert th.push_stage(nodes, date(2026, 11, 10)) is None


@pytest.fixture
def soon(monkeypatch):
    """Транзит узлов, который начнётся через 5 дней от сегодняшней даты."""
    nodes = next(t for t in TS if t.planet == "Ra")
    now = datetime.now(timezone.utc)
    t = dataclasses.replace(nodes, start=now + timedelta(days=6), start_true=now + timedelta(days=5))
    monkeypatch.setattr(th, "current", lambda now=None: [t])
    monkeypatch.setattr(th, "PUSH_HOUR", 0)
    return t


@pytest.mark.asyncio
async def test_transits_command_and_personal_paywall(tg, repo, soon):
    dp, bot, fake, _ = tg
    await register(dp, bot)
    fake.calls.clear()
    await dp.feed_update(bot, msg(U, "/transits"))
    kbd = fake.of(SendMessage)[-1].reply_markup.inline_keyboard
    assert kbd[0][0].callback_data == f"tr:{soon.key}"
    await dp.feed_update(bot, cb(U, f"tr:{soon.key}"))
    last = fake.of(SendMessage)[-1]
    assert "Смена оси узлов" in last.text and "start=g_" in last.text
    await dp.feed_update(bot, cb(U, f"trp:{soon.key}"))
    assert "по вашей карте" in fake.texts(U)[-1]                     # пробный Премиум после регистрации
    await repo.pool.execute("UPDATE users SET premium_until = NULL WHERE tg_id = $1", U)
    await dp.feed_update(bot, cb(U, f"trp:{soon.key}"))
    assert fake.texts(U)[-1].startswith("🔒")


@pytest.mark.asyncio
async def test_push_teaser_once(tg, repo, soon):
    dp, bot, fake, _ = tg
    await register(dp, bot)
    fake.calls.clear()
    assert await th.send_transit_pushes(bot, repo) == 1
    assert await th.send_transit_pushes(bot, repo) == 0
    txt = re.sub(r"<[^>]+>", "", fake.texts(U)[-1])
    assert "Смена оси узлов" in txt and "уже скоро" in txt or "через неделю" in txt


@pytest.mark.asyncio
async def test_forecast_has_transits_button(tg):
    dp, bot, fake, _ = tg
    await register(dp, bot)
    fake.calls.clear()
    await dp.feed_update(bot, msg(U, "/forecast"))
    kbd = [c for c in fake.of(SendMessage) if "Новолуние" in c.text][0].reply_markup.inline_keyboard
    assert any(b.callback_data == "tr:list" for row in kbd for b in row)


def test_saturn_to_aries_2027():
    ts = big_transits(datetime(2027, 5, 20, tzinfo=MSK))
    sa = next(t for t in ts if t.planet == "Sa")
    assert (sa.prev_rashi, sa.rashi) == (11, 0) and sa.start.date() == date(2027, 6, 3)
    assert [(a.date(), b.date()) for a, b in sa.returns] == [(date(2027, 10, 20), date(2028, 2, 23))]
    from bot.transits_view import render_for_sign, teaser
    assert "Саде-Сати" in render_for_sign(sa, 11)          # Рыбы: Сатурн во 2-м — третья фаза
    assert "Саде-Сати" in teaser(sa, 7)


def test_retrograde_return_is_not_a_new_transit():
    ts = big_transits(datetime(2027, 2, 1, tzinfo=MSK))
    assert [t.key for t in ts if t.planet == "Ju"] == ["jupiter-2026-10"]


def test_saturn_texts_complete():
    from jyotish.transits import SATURN
    assert set(SATURN) == set(range(1, 13))
    assert all({"theme", "money", "love", "practice"} <= set(v) for v in SATURN.values())
