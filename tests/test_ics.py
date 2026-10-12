"""Выгрузка астрокалендаря в .ics."""
from datetime import date

import pytest
from aiogram.methods import SendDocument

from bot.astro_service import settings_for
from bot.ics import build_ics
from jyotish.profile import compute
from tests.conftest import cb, msg
from tests.test_bot_flow import U, register


def test_ics_structure_and_content():
    from datetime import datetime
    prof = compute(datetime(1980, 5, 14, 6, 30), 59.93, 30.33, "Europe/Moscow", True)
    data = build_ics(date(2026, 10, 12), settings_for("moscow"), 6, 15, prof, "ru").decode("utf-8")
    assert data.startswith("BEGIN:VCALENDAR\r\n") and data.rstrip().endswith("END:VCALENDAR")
    assert data.count("BEGIN:VEVENT") == data.count("END:VEVENT") > 10
    unfolded = data.replace("\r\n ", "")
    for marker in ("Юпитер → Лев", "Полнолуние", "Экадаши", "Kai Tara"):
        assert marker in unfolded, marker
    assert all(len(line.encode("utf-8")) <= 75 for line in data.split("\r\n"))     # RFC 5545


@pytest.mark.asyncio
async def test_ics_from_month_and_calendar(tg, repo):
    dp, bot, fake, _ = tg
    await register(dp, bot)
    await dp.feed_update(bot, msg(U, "/month"))
    kbd = fake.of(type(fake.calls[-1]))[-1].reply_markup.inline_keyboard
    assert any(b.callback_data == "ics:get" for row in kbd for b in row)
    fake.calls.clear()
    await dp.feed_update(bot, cb(U, "ics:get"))
    docs = fake.of(SendDocument)
    assert docs and docs[0].document.filename == "kai_tara.ics"
