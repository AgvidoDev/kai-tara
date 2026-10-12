"""Натальная карта: картинка, таблица, сценарий в боте; введённые данные не сохраняются."""
import io
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from aiogram.methods import SendMessage, SendPhoto
from PIL import Image

from bot.chart_view import render_png, render_text
from jyotish.core import Location
from jyotish.natal import build_chart
from tests.conftest import cb, msg
from tests.test_bot_flow import U, register

CYR = re.compile(r"[А-Яа-яЁё]")
LOC = Location("СПб", 59.93, 30.33, "Europe/Moscow")
CH = build_chart(datetime(1980, 5, 14, 6, 30, tzinfo=ZoneInfo("Europe/Moscow")), LOC)
NOW = datetime(2026, 10, 11, tzinfo=ZoneInfo("UTC"))


@pytest.mark.parametrize("lang", ["ru", "en"])
@pytest.mark.parametrize("known", [True, False])
def test_png_is_valid(lang, known):
    img = Image.open(io.BytesIO(render_png(CH, lang, known, "X")))
    assert img.format == "PNG" and img.size == (960, 960)


def test_text_lists_all_planets():
    ru, en = render_text(CH, NOW, "ru"), render_text(CH, NOW, "en")
    for name in ("Солнце", "Луна", "Марс", "Меркурий", "Юпитер", "Венера", "Сатурн", "Раху", "Кету"):
        assert name in ru
    for name in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"):
        assert name in en
    assert not CYR.search(en)
    assert "Близнецы 9°" in ru and "Махадаша: Юпитер" in re.sub(r"<[^>]+>", "", ru)


def test_text_without_time_counts_houses_from_moon():
    ch = build_chart(datetime(1980, 5, 14, 12, 0, tzinfo=ZoneInfo("Europe/Moscow")), LOC)
    txt = render_text(ch, NOW, "ru", time_known=False)
    assert "от Луны" in txt and "Махадаша" not in txt


async def _flow(dp, bot, uid, lang, city):
    await dp.feed_update(bot, msg(uid, "/chart", lang=lang))
    await dp.feed_update(bot, msg(uid, "14.05.1980", lang=lang))
    await dp.feed_update(bot, msg(uid, "06:30", lang=lang))
    await dp.feed_update(bot, cb(uid, f"cplace:{city}", lang=lang))


@pytest.mark.asyncio
@pytest.mark.parametrize("lang,city", [("ru", "spb"), ("en", "london")])
async def test_chart_flow_sends_photo_and_text(tg, repo, lang, city):
    dp, bot, fake, _ = tg
    await register(dp, bot)
    await dp.feed_update(bot, cb(U, f"lang:{lang}"))                 # язык выбран явно
    before = await repo.pool.fetchrow("SELECT * FROM profiles")
    fake.calls.clear()
    await _flow(dp, bot, U, lang, city)
    photos = fake.of(SendPhoto)
    assert photos and photos[0].photo.filename == "chart.png"
    text = [c.text for c in fake.of(SendMessage) if "°" in (c.text or "")][0]
    assert ("Планеты в вашей карте" if lang == "ru" else "Planets in your chart") in text
    assert "start=g_" in text                                      # термины кликабельны
    after = await repo.pool.fetchrow("SELECT * FROM profiles")
    assert dict(before) == dict(after)                             # профиль не тронут, ввод не сохранён


@pytest.mark.asyncio
async def test_my_chart_has_build_button(tg, repo):
    dp, bot, fake, _ = tg
    await register(dp, bot)
    fake.calls.clear()
    await dp.feed_update(bot, msg(U, "/me"))
    kbd = fake.of(SendMessage)[-1].reply_markup.inline_keyboard
    assert kbd[0][0].callback_data == "chart:new"
