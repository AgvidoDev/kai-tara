"""Английская версия: каталог строк, словарь и сквозной путь пользователя без кириллицы."""
import re
import string

import pytest
from aiogram.methods import SendMessage

from bot.i18n import M, detect, t
from jyotish.glossary import terms
from tests.conftest import cb, msg

CYR = re.compile(r"[А-Яа-яЁё]")
E = 777


def fields(s: str) -> set[str]:
    return {f for _, f, _, _ in string.Formatter().parse(s) if f}


def test_catalog_complete_and_placeholders_match():
    for key, v in M.items():
        assert set(v) == {"ru", "en"}, key
        assert fields(v["ru"]) == fields(v["en"]), key
        assert not CYR.search(v["en"]), key


def test_detect_language():
    assert detect("ru") == detect("uk") == detect("kk") == "ru"
    assert detect("en-GB") == detect("de") == detect(None) == "en"


def test_glossary_has_same_terms_in_both_languages():
    assert set(terms("ru")) == set(terms("en"))
    for term in terms("en").values():
        assert not CYR.search(term.title + term.short + term.long), term.key


async def en_register(dp, bot, uid=E):
    await dp.feed_update(bot, msg(uid, "/start", lang="en"))
    await dp.feed_update(bot, cb(uid, "consent:yes", lang="en"))
    await dp.feed_update(bot, msg(uid, "14.05.1980", lang="en"))
    await dp.feed_update(bot, msg(uid, "06:30", lang="en"))
    await dp.feed_update(bot, cb(uid, "bplace:london", lang="en"))


def no_cyrillic(texts):
    bad = [x for x in texts if CYR.search(re.sub(r"<[^>]+>", "", x))]
    assert not bad, bad[:2]


@pytest.mark.asyncio
async def test_english_user_journey(tg, repo):
    dp, bot, fake, cfg = tg
    await en_register(dp, bot)
    u = await repo.get_user(E)
    assert u["lang"] == "en" and u["city_key"] == "london"
    for cmd in ("/forecast", "/today", "/personal", "/calendar", "/me", "/premium", "/transits", "/glossary",
                "/help", "/terms", "/privacy", "/settings"):
        await dp.feed_update(bot, msg(E, cmd, lang="en"))
    await dp.feed_update(bot, msg(E, "/start g_sade_sati", lang="en"))
    await dp.feed_update(bot, cb(E, "gll", text="Saturn in the 8th house, Vishakha nakshatra", lang="en"))
    texts = fake.texts(E)
    no_cyrillic(texts)
    joined = "\n".join(texts)
    for marker in ("I'm Kai Tara", "Done! Your chart", "New Moon", "Today,", "Personal forecast",
                   "Favourable days", "Astro Premium", "Major transits", "Jyotish glossary", "Sade Sati",
                   "Privacy policy", "(London)"):
        assert marker in joined, marker
    assert "start=g_" in joined                                   # ссылки на английский словарь


@pytest.mark.asyncio
async def test_english_compat_and_menu_buttons(tg, repo):
    dp, bot, fake, cfg = tg
    await en_register(dp, bot)
    fake.calls.clear()
    await dp.feed_update(bot, msg(E, "💞 Compatibility", lang="en"))       # кнопка меню на английском
    await dp.feed_update(bot, cb(E, "cg:m", lang="en"))
    await dp.feed_update(bot, msg(E, "02.03.1985", lang="en"))
    await dp.feed_update(bot, cb(E, "ptime:unknown", lang="en"))
    await dp.feed_update(bot, cb(E, "pplace:new_york", lang="en"))
    texts = fake.texts(E)
    no_cyrillic(texts)
    assert any("of 36" in x for x in texts)


@pytest.mark.asyncio
async def test_switch_language(tg, repo):
    dp, bot, fake, cfg = tg
    await en_register(dp, bot)
    await dp.feed_update(bot, cb(E, "lang:ru", lang="en"))
    assert (await repo.get_lang(E)) == "ru"
    fake.calls.clear()
    await dp.feed_update(bot, msg(E, "/today", lang="en"))      # язык Telegram уже не важен — выбран русский
    assert "Сегодня" in fake.texts(E)[-1]
    await dp.feed_update(bot, cb(E, "lang:en"))
    fake.calls.clear()
    await dp.feed_update(bot, msg(E, "☀️ Сегодня"))             # русская кнопка тоже работает
    assert "Today" in fake.texts(E)[-1]


@pytest.mark.asyncio
async def test_pushes_follow_user_language(tg, repo):
    from bot.broadcast import send_daily
    dp, bot, fake, cfg = tg
    await en_register(dp, bot)
    cfg.daily_hour = 0
    fake.calls.clear()
    assert await send_daily(bot, repo, cfg) == 1
    sent = [c for c in fake.of(SendMessage) if c.chat_id == E]
    assert sent and "Today" in sent[-1].text and not CYR.search(re.sub(r"<[^>]+>", "", sent[-1].text))


@pytest.mark.asyncio
async def test_english_paywall(tg, repo):
    dp, bot, fake, cfg = tg
    await en_register(dp, bot)
    await repo.pool.execute("UPDATE users SET premium_until = NULL WHERE tg_id = $1", E)
    fake.calls.clear()
    await dp.feed_update(bot, msg(E, "/calendar", lang="en"))
    last = fake.of(SendMessage)[-1]
    assert "is a Premium feature" in last.text
    assert any("Premium —" in b.text for row in last.reply_markup.inline_keyboard for b in row)
    assert t("en", "kb_buy_premium", price=199) == "💎 Premium — 199 ⭐ / 30 days"
