"""Близкие: добавление без хранения даты рождения, карточка, день, совместимость, удаление, лимит."""
from datetime import date

import pytest
from aiogram.methods import SendMessage

from bot import keyboards as kb
from tests.conftest import cb, msg
from tests.test_bot_flow import U, register


def _buttons(fake) -> list[str]:
    out = []
    for c in fake.of(SendMessage):
        mk = c.reply_markup
        for row in getattr(mk, "inline_keyboard", None) or []:
            out += [b.callback_data for b in row]
    return out


async def _add(dp, bot, name="Мама", day="03.02.1955", time="08:15"):
    await dp.feed_update(bot, cb(U, "rel:add"))
    await dp.feed_update(bot, msg(U, name))
    await dp.feed_update(bot, msg(U, day))
    if time:
        await dp.feed_update(bot, msg(U, time))
    else:
        await dp.feed_update(bot, cb(U, "rtime:unknown"))
    await dp.feed_update(bot, cb(U, "rplace:spb"))


@pytest.mark.asyncio
async def test_add_relative_stores_only_profile(tg, repo):
    dp, bot, fake, cfg = tg
    await register(dp, bot)
    cfg.free_until = date(2099, 1, 1)
    fake.calls.clear()
    await dp.feed_update(bot, msg(U, "👨‍👩‍👧 Близкие"))
    assert "Добавьте родных" in fake.texts(U)[-1] and "rel:add" in _buttons(fake)
    await _add(dp, bot)
    assert any("Профиль «Мама» сохранён" in x for x in fake.texts(U))
    (rid, name), = await repo.relatives(U)
    assert name == "Мама"
    cols = {r["column_name"] for r in await repo.pool.fetch(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'relatives'")}
    assert not cols & {"birth_date", "birth_time", "birth_enc", "lat", "lon", "place"}
    _, prof = await repo.get_relative(U, rid)
    assert prof.time_known and prof.moon is not None and prof.dashas
    assert f"rel:day:{rid}" in _buttons(fake)


@pytest.mark.asyncio
async def test_relative_day_compat_and_delete(tg, repo):
    dp, bot, fake, cfg = tg
    await register(dp, bot)
    cfg.free_until = date(2099, 1, 1)
    await _add(dp, bot, name="Саша <b>")
    (rid, _), = await repo.relatives(U)
    fake.calls.clear()
    await dp.feed_update(bot, cb(U, f"rel:day:{rid}"))
    assert "Саша &lt;b&gt;:" in fake.texts(U)[-1]
    fake.calls.clear()
    await dp.feed_update(bot, cb(U, f"rel:cmp:{rid}"))
    await dp.feed_update(bot, cb(U, f"relc:m:{rid}"))
    assert "/36" in fake.texts(U)[-1] or "36" in fake.texts(U)[-1]
    await dp.feed_update(bot, cb(U, f"rel:del:{rid}"))
    await dp.feed_update(bot, cb(U, f"rel:delok:{rid}"))
    assert await repo.relatives(U) == []


@pytest.mark.asyncio
async def test_relative_without_time_and_compat_needs_moon(tg, repo):
    dp, bot, fake, cfg = tg
    await register(dp, bot)
    cfg.free_until = date(2099, 1, 1)
    await _add(dp, bot, name="Друг", day="15.06.1990", time=None)
    (rid, _), = await repo.relatives(U)
    _, prof = await repo.get_relative(U, rid)
    assert not prof.time_known and not prof.dashas


@pytest.mark.asyncio
async def test_other_user_cannot_see_relative(tg, repo):
    dp, bot, fake, cfg = tg
    await register(dp, bot)
    cfg.free_until = date(2099, 1, 1)
    await _add(dp, bot)
    (rid, _), = await repo.relatives(U)
    assert await repo.get_relative(U + 1, rid) is None
    assert not await repo.delete_relative(U + 1, rid)
    await repo.delete_user(U)                                     # удаление аккаунта стирает и близких
    assert await repo.pool.fetchval("SELECT count(*) FROM relatives") == 0


@pytest.mark.asyncio
async def test_limit(tg, repo):
    from bot.relatives import LIMIT
    from jyotish.profile import compute
    from datetime import datetime
    dp, bot, fake, cfg = tg
    await register(dp, bot)
    p = compute(datetime(1990, 1, 1, 12), 59.9, 30.3, "Europe/Moscow", True)
    for i in range(LIMIT):
        assert await repo.add_relative(U, f"n{i}", p, LIMIT)
    assert await repo.add_relative(U, "extra", p, LIMIT) is None


@pytest.mark.asyncio
async def test_bad_name_rejected(tg, repo):
    dp, bot, fake, cfg = tg
    await register(dp, bot)
    cfg.free_until = date(2099, 1, 1)
    await dp.feed_update(bot, cb(U, "rel:add"))
    await dp.feed_update(bot, msg(U, "x" * 40))
    assert "от 1 до 32" in fake.texts(U)[-1]


def test_menu_hides_premium_in_free_mode(monkeypatch):
    def labels():
        return [b.text for row in kb.main_menu("ru").keyboard for b in row]
    monkeypatch.setattr(kb, "SHOW_PREMIUM", False)
    assert "💎 Премиум" not in labels() and "👨‍👩‍👧 Близкие" in labels()
    monkeypatch.setattr(kb, "SHOW_PREMIUM", True)
    assert "💎 Премиум" in labels()


@pytest.mark.asyncio
async def test_help_without_premium_in_free_mode(tg, repo):
    dp, bot, fake, cfg = tg
    cfg.free_mode = True
    await dp.feed_update(bot, msg(U, "/help"))
    text = fake.texts(U)[-1]
    assert "/family" in text and "/premium" not in text and "💎" not in text
