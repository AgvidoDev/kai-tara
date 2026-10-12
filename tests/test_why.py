"""«Почему так?»: раскрытие факторов прогноза на лунацию и дня."""
import re

import pytest
from aiogram.methods import SendMessage

from tests.conftest import cb, msg
from tests.test_bot_flow import U, register

CYR = re.compile(r"[А-Яа-яЁё]")


def plain(s):
    return re.sub(r"<[^>]+>", "", s)


@pytest.mark.asyncio
async def test_forecast_why_lists_factors(tg, repo):
    dp, bot, fake, _ = tg
    await register(dp, bot)
    await dp.feed_update(bot, msg(U, "/forecast"))
    kbd = [c for c in fake.of(SendMessage) if "Новолуние" in (c.text or "")][-1].reply_markup.inline_keyboard
    assert any(b.callback_data == "why:lun" for row in kbd for b in row)
    fake.calls.clear()
    await dp.feed_update(bot, cb(U, "why:lun"))
    text = plain(fake.texts(U)[-1])
    assert "Почему такой прогноз" in text and "Итого" in text
    for planet in ("Солнце", "Марс", "Юпитер", "Сатурн", "Раху", "Кету"):
        assert planet in text
    assert "хорош в" in text


@pytest.mark.asyncio
async def test_today_why_explains_tara_and_chandra(tg, repo):
    dp, bot, fake, _ = tg
    await register(dp, bot)
    await dp.feed_update(bot, msg(U, "/today"))
    kbd = fake.of(SendMessage)[-1].reply_markup.inline_keyboard
    assert any(b.callback_data == "why:day" for row in kbd for b in row)
    fake.calls.clear()
    await dp.feed_update(bot, cb(U, "why:day"))
    text = plain(fake.texts(U)[-1])
    assert "Тара-бала" in text and "Чандра-бала" in text and "Титхи" in text and "Итого" in text


@pytest.mark.asyncio
async def test_why_in_english(tg, repo):
    dp, bot, fake, _ = tg
    await register(dp, bot)
    await dp.feed_update(bot, cb(U, "lang:en"))
    fake.calls.clear()
    await dp.feed_update(bot, cb(U, "why:lun"))
    await dp.feed_update(bot, cb(U, "why:day"))
    texts = [plain(x) for x in fake.texts(U)]
    assert any("Why this forecast" in x for x in texts) and any("Why this day" in x for x in texts)
    assert not any(CYR.search(x) for x in texts)


@pytest.mark.asyncio
async def test_why_day_is_premium_even_if_button_forged(tg, repo):
    dp, bot, fake, cfg = tg
    await register(dp, bot)
    await repo.pool.execute("UPDATE users SET premium_until = NULL WHERE tg_id = $1", U)
    fake.calls.clear()
    await dp.feed_update(bot, cb(U, "why:day"))                    # подделанное нажатие
    assert fake.texts(U)[-1].startswith("🔒")
    assert not any("Тара-бала:" in x for x in fake.texts(U))
