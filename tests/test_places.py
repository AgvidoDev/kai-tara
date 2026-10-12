"""Поиск города по названию (GeoNames) и ввод места во всех сценариях бота."""
import pytest
from aiogram.methods import SendMessage, SendPhoto

from jyotish import geo
from tests.conftest import cb, msg
from tests.test_bot_flow import U

KAZAN = geo.search("Казань")[0]


def test_search_basics():
    assert KAZAN.ru == "Казань" and KAZAN.region_ru == "Республика Татарстан" and KAZAN.tz == "Europe/Moscow"
    assert geo.search("спб")[0].ru == "Санкт-Петербург"
    assert geo.search("ёлкино")[0].ru.startswith("Елкино")                    # ё = е
    assert geo.search("Київ")[0].ru == "Киев"                                 # украинское написание
    assert geo.search("london")[0].label("en") == "London, England, GB"
    assert len(geo.search("Октябрьский")) > 3
    assert [c.region_ru for c in geo.search("Октябрьский, перм")] == ["Пермский край"]
    assert geo.search("Ыыыыщщщ") == [] and geo.search("М") == []
    assert geo.by_key(KAZAN.key) == KAZAN


async def _reg_until_place(dp, bot, uid=U):
    await dp.feed_update(bot, msg(uid, "/start"))
    await dp.feed_update(bot, cb(uid, "consent:yes"))
    await dp.feed_update(bot, msg(uid, "14.05.1980"))
    await dp.feed_update(bot, msg(uid, "06:30"))


@pytest.mark.asyncio
async def test_registration_by_city_name(tg, repo):
    dp, bot, fake, _ = tg
    await _reg_until_place(dp, bot)
    await dp.feed_update(bot, msg(U, "Казань"))
    assert (await repo.get_user(U))["has_birth"]
    assert any("📍 Казань, Республика Татарстан" in x for x in fake.texts(U))


@pytest.mark.asyncio
async def test_ambiguous_city_offers_buttons(tg, repo):
    dp, bot, fake, _ = tg
    await _reg_until_place(dp, bot)
    fake.calls.clear()
    await dp.feed_update(bot, msg(U, "Октябрьский"))
    kbd = fake.of(SendMessage)[-1].reply_markup.inline_keyboard
    assert len(kbd) >= 3 and all(row[0].callback_data.startswith("bplace:gn") for row in kbd)
    assert not (await repo.get_user(U))["has_birth"]
    await dp.feed_update(bot, cb(U, kbd[1][0].callback_data))                  # выбрали второй
    assert (await repo.get_user(U))["has_birth"]


@pytest.mark.asyncio
async def test_city_not_found(tg, repo):
    dp, bot, fake, _ = tg
    await _reg_until_place(dp, bot)
    await dp.feed_update(bot, msg(U, "Ыыыыщщщ"))
    assert "Не нашёл" in fake.texts(U)[-1]
    await dp.feed_update(bot, msg(U, "55.75, 37.62"))                          # координаты по-прежнему работают
    assert (await repo.get_user(U))["has_birth"]


@pytest.mark.asyncio
async def test_chart_by_city_name(tg, repo):
    dp, bot, fake, _ = tg
    await dp.feed_update(bot, msg(U, "/chart"))
    await dp.feed_update(bot, msg(U, "14.05.1980"))
    await dp.feed_update(bot, msg(U, "06:30"))
    await dp.feed_update(bot, msg(U, "Ялта"))                                  # две Ялты — выбор
    kbd = fake.of(SendMessage)[-1].reply_markup.inline_keyboard
    await dp.feed_update(bot, cb(U, kbd[0][0].callback_data))
    assert fake.of(SendPhoto)


@pytest.mark.asyncio
async def test_settings_city_by_name_used_in_forecast(tg, repo):
    from tests.test_bot_flow import register
    dp, bot, fake, _ = tg
    await register(dp, bot)
    await dp.feed_update(bot, cb(U, "set:city"))
    await dp.feed_update(bot, msg(U, "Новосибирск"))
    u = await repo.get_user(U)
    assert u["city_key"].startswith("gn") and u["tz"] == "Asia/Novosibirsk"
    fake.calls.clear()
    await dp.feed_update(bot, msg(U, "/forecast"))
    assert any("Новосибирск" in (c.text or "") for c in fake.of(SendMessage))
