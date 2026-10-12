"""Прогноз на 7 дней и на месяц."""
import re
from datetime import date

import pytest
from aiogram.methods import SendMessage

from bot.astro_service import settings_for
from bot.period_view import build_period, month_bounds, render_month, render_week
from tests.conftest import cb, msg
from tests.test_bot_flow import U, register

CYR = re.compile(r"[А-Яа-яЁё]")
S = settings_for("moscow")


def test_week_has_seven_days_and_events():
    per = build_period(date(2026, 10, 12), date(2026, 10, 18), S, 6, 15)
    assert len(per.days) == 7
    txt = render_week(per, "ru", "Москва")
    assert txt.count("(пн)") + txt.count("(вт)") + txt.count("(ср)") >= 3
    assert "Солнце → Весы" in txt and "Лучший день" in txt
    assert not CYR.search(re.sub(r"<[^>]+>", "", render_week(per, "en", "Moscow")))


def test_month_bounds_and_content():
    a, b = month_bounds(date(2026, 10, 12))
    assert (a, b) == (date(2026, 10, 12), date(2026, 10, 31))
    per = build_period(a, b, S, 6, 15)
    txt = render_month(per, "ru", "Москва", "⏳ Махадаша <b>Юпитер</b>", ["🪐 Юпитер → Лев"])
    assert "Ваши лучшие дни" in txt and "Юпитер → Лев" in txt and "Полнолуние" in txt


@pytest.mark.asyncio
async def test_week_and_month_from_today_buttons(tg, repo):
    dp, bot, fake, _ = tg
    await register(dp, bot)
    await dp.feed_update(bot, msg(U, "/today"))
    kbd = fake.of(SendMessage)[-1].reply_markup.inline_keyboard
    datas = {b.callback_data for row in kbd for b in row}
    assert {"per:week", "per:month"} <= datas
    fake.calls.clear()
    await dp.feed_update(bot, cb(U, "per:week"))
    await dp.feed_update(bot, msg(U, "/month"))
    texts = fake.texts(U)
    assert any("Ваши 7 дней" in x for x in texts) and any("Месяц: до" in x for x in texts)


@pytest.mark.asyncio
async def test_period_is_premium(tg, repo):
    dp, bot, fake, _ = tg
    await register(dp, bot)
    await repo.pool.execute("UPDATE users SET premium_until = NULL WHERE tg_id = $1", U)
    fake.calls.clear()
    await dp.feed_update(bot, cb(U, "per:month"))
    assert fake.texts(U)[-1].startswith("🔒")
