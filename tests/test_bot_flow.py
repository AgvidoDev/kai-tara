"""Сквозные сценарии бота на живом PostgreSQL с подменённым Telegram API."""
import re
from datetime import datetime, timedelta, timezone

import pytest
from aiogram.methods import AnswerPreCheckoutQuery, SendInvoice, SendMessage
from aiogram.types import PreCheckoutQuery, SuccessfulPayment, Update, User

from tests.conftest import cb, msg

pytestmark = pytest.mark.asyncio
U = 555


async def register(dp, bot, uid=U, start="/start", time="06:30"):
    await dp.feed_update(bot, msg(uid, start))
    await dp.feed_update(bot, cb(uid, "consent:yes"))
    await dp.feed_update(bot, msg(uid, "14.05.1980"))
    await dp.feed_update(bot, msg(uid, time))
    await dp.feed_update(bot, cb(uid, "bplace:spb"))


async def test_registration_gives_trial_once(tg, repo):
    dp, bot, fake, cfg = tg
    await register(dp, bot)
    u = await repo.get_user(U)
    assert u["has_birth"] and u["trial_used"]
    assert u["premium_until"] > datetime.now(timezone.utc) + timedelta(days=2)
    assert any("Дарим 3 дня Премиума" in t for t in fake.texts(U))
    first_until = u["premium_until"]
    await dp.feed_update(bot, cb(U, "set:birth"))          # повторный ввод данных
    await dp.feed_update(bot, msg(U, "14.05.1980"))
    await dp.feed_update(bot, msg(U, "06:30"))
    await dp.feed_update(bot, cb(U, "bplace:spb"))
    assert (await repo.get_user(U))["premium_until"] == first_until


async def test_forecast_has_term_links_and_button(tg, repo):
    dp, bot, fake, _ = tg
    await register(dp, bot)
    fake.calls.clear()
    await dp.feed_update(bot, msg(U, "/forecast"))
    sent = [c for c in fake.of(SendMessage) if "Новолуние" in c.text]
    assert sent, fake.texts()
    assert "https://t.me/astro_test_bot?start=g_" in sent[0].text
    assert sent[0].reply_markup.inline_keyboard[0][0].callback_data == "gll"


async def test_glossary_deeplink_and_buttons(tg):
    dp, bot, fake, _ = tg
    await dp.feed_update(bot, msg(U, "/start g_sade_sati"))
    assert any("Саде-Сати" in t for t in fake.texts(U))
    fake.calls.clear()
    await dp.feed_update(bot, cb(U, "gll", text="Сатурн в 8-м доме, накшатра Вишакха"))
    kbd = fake.of(SendMessage)[0].reply_markup.inline_keyboard
    datas = {b.callback_data for row in kbd for b in row}
    assert {"gl:saturn", "gl:house_8", "gl:nakshatra", "gl:vishakha"} <= datas
    await dp.feed_update(bot, msg(U, "/glossary"))
    await dp.feed_update(bot, cb(U, "gl:tarabala"))
    assert any("Тара-бала" in t for t in fake.texts(U))


async def test_free_user_hits_paywalls(tg, repo):
    dp, bot, fake, _ = tg
    await register(dp, bot)
    await repo.pool.execute("UPDATE users SET premium_until = now() - interval '1 day' WHERE tg_id = $1", U)
    fake.calls.clear()
    for cmd in ("/personal", "/calendar", "/compat"):
        await dp.feed_update(bot, msg(U, cmd))
    paywalls = [t for t in fake.texts(U) if t.startswith("🔒")]
    assert len(paywalls) == 3
    await dp.feed_update(bot, msg(U, "/today"))
    today = fake.texts(U)[-1]
    assert "Сегодня" in today and "В Премиуме" in today and "Хорошо для" not in today


async def test_premium_features(tg, repo):
    dp, bot, fake, _ = tg
    await register(dp, bot)
    fake.calls.clear()
    await dp.feed_update(bot, msg(U, "/today"))
    assert "Хорошо для" in fake.texts(U)[-1]
    await dp.feed_update(bot, msg(U, "/calendar"))
    assert "Благоприятные дни" in fake.texts(U)[-1]
    await dp.feed_update(bot, msg(U, "/personal"))
    assert "Упаи" in fake.texts(U)[-1]


async def test_compat_flow_with_credit(tg, repo):
    dp, bot, fake, _ = tg
    await register(dp, bot)
    await repo.pool.execute("UPDATE users SET premium_until = NULL, compat_credits = 1 WHERE tg_id = $1", U)
    await dp.feed_update(bot, msg(U, "/compat"))
    await dp.feed_update(bot, cb(U, "cg:f"))
    await dp.feed_update(bot, msg(U, "02.03.1985"))
    await dp.feed_update(bot, cb(U, "ptime:unknown"))
    await dp.feed_update(bot, cb(U, "pplace:moscow"))
    res = [re.sub(r"<[^>]+>", "", t) for t in fake.texts(U) if "из 36" in t]
    assert res and "из 36" in res[0] and "неточна" in res[0]
    assert (await repo.get_user(U))["compat_credits"] == 0
    fake.calls.clear()
    await dp.feed_update(bot, msg(U, "/compat"))          # кредитов нет — пейволл с разовой покупкой
    kbd = fake.of(SendMessage)[-1].reply_markup.inline_keyboard
    assert any(b.callback_data == "buy:compat" for row in kbd for b in row)


def _payment_update(uid, payload, amount, charge, recurring=False, exp=None):
    sp = SuccessfulPayment(currency="XTR", total_amount=amount, invoice_payload=payload,
                           telegram_payment_charge_id=charge, provider_payment_charge_id="",
                           is_recurring=recurring or None, is_first_recurring=recurring or None,
                           subscription_expiration_date=exp)
    return msg(uid, None, successful_payment=sp)


async def test_payments_subscription_and_compat(tg, repo):
    dp, bot, fake, cfg = tg
    await register(dp, bot)
    # pre_checkout: верная и неверная цена
    for amount, ok in ((cfg.price_premium, True), (1, False)):
        q = PreCheckoutQuery(id=f"q{amount}", from_user=User(id=U, is_bot=False, first_name="U"),
                             currency="XTR", total_amount=amount, invoice_payload="premium_sub")
        fake.calls.clear()
        await dp.feed_update(bot, Update(update_id=10_000 + amount, pre_checkout_query=q))
        assert fake.of(AnswerPreCheckoutQuery)[0].ok is ok
    exp = int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp())
    upd = _payment_update(U, "premium_sub", cfg.price_premium, "ch_1", recurring=True, exp=exp)
    await dp.feed_update(bot, upd)
    await dp.feed_update(bot, upd)                         # повторная доставка — без дублей
    u = await repo.get_user(U)
    assert u["sub_charge_id"] == "ch_1" and u["premium_until"].timestamp() >= exp - 1
    assert await repo.pool.fetchval("SELECT count(*) FROM payments") == 1
    await dp.feed_update(bot, cb(U, "buy:compat"))
    assert fake.of(SendInvoice)[-1].currency == "XTR"
    await dp.feed_update(bot, _payment_update(U, "compat", cfg.price_compat, "ch_2"))
    assert (await repo.get_user(U))["compat_credits"] == 1
    await dp.feed_update(bot, cb(U, "sub:cancel"))
    assert (await repo.get_user(U))["sub_canceled"]


async def test_referral_bonus(tg, repo):
    dp, bot, fake, cfg = tg
    await register(dp, bot, uid=100)
    before = (await repo.get_user(100))["premium_until"]
    await register(dp, bot, uid=200, start="/start ref_100")
    after = (await repo.get_user(100))["premium_until"]
    assert after - before >= timedelta(days=cfg.ref_bonus_days) - timedelta(seconds=5)
    assert any("друг присоединился" in t for t in fake.texts(100))
    await register(dp, bot, uid=300, start="/start ref_300")   # сам себя не приглашает
    assert (await repo.get_user(300))["referred_by"] is None


async def test_daily_push_once_per_day(tg, repo):
    from bot.broadcast import send_daily
    dp, bot, fake, cfg = tg
    await register(dp, bot)
    cfg.daily_hour = 0
    assert await send_daily(bot, repo, cfg) == 1
    assert await send_daily(bot, repo, cfg) == 0
    await repo.set_daily_push(U, False)
    await repo.pool.execute("DELETE FROM daily_sent")
    assert await send_daily(bot, repo, cfg) == 0


async def test_admin_commands(tg, repo):
    dp, bot, fake, _ = tg
    await register(dp, bot)
    await dp.feed_update(bot, msg(999, f"/grant {U} 10"))
    assert any("Премиум до" in t for t in fake.texts(999))
    await dp.feed_update(bot, msg(999, "/stats"))
    assert any("Премиум активен" in t for t in fake.texts(999))
    fake.calls.clear()
    await dp.feed_update(bot, msg(U, "/stats"))              # не админ — команда игнорируется
    assert not any("Премиум активен" in t for t in fake.texts(U))


async def test_delete_removes_user_but_keeps_payments(tg, repo):
    dp, bot, fake, cfg = tg
    await register(dp, bot)
    await dp.feed_update(bot, _payment_update(U, "compat", cfg.price_compat, "ch_9"))
    await dp.feed_update(bot, cb(U, "del:yes"))
    assert await repo.get_user(U) is None
    assert await repo.pool.fetchval("SELECT count(*) FROM payments") == 1


async def test_admin_subs_lists_paying_and_trial(tg, repo):
    from aiogram.methods import SendDocument
    dp, bot, fake, cfg = tg
    await register(dp, bot, uid=100)                       # пробный период
    await register(dp, bot, uid=200)
    exp = int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp())
    await dp.feed_update(bot, _payment_update(200, "premium_sub", cfg.price_premium, "s1", True, exp))
    await register(dp, bot, uid=300)
    await repo.pool.execute("UPDATE users SET premium_until = NULL WHERE tg_id = 300")
    fake.calls.clear()
    await dp.feed_update(bot, msg(999, "/subs"))
    out = "\n".join(fake.texts(999))
    assert "Платящие: 1" in out and "200" in out and "@user200" in out and "199⭐" in out
    assert "Пробный период и подарки: 1" in out and "100" in out
    assert "300" not in out
    fake.calls.clear()
    await dp.feed_update(bot, msg(999, "/subs paid"))
    out = "\n".join(fake.texts(999))
    assert "200" in out and "Пробный" not in out
    fake.calls.clear()
    await dp.feed_update(bot, msg(999, "/subs all"))
    out = "\n".join(fake.texts(999))
    assert all(str(i) in out for i in (100, 200, 300))
    fake.calls.clear()
    await dp.feed_update(bot, msg(999, "/subs csv"))
    doc = fake.of(SendDocument)
    assert doc and doc[0].document.filename.endswith(".csv")
    fake.calls.clear()
    await dp.feed_update(bot, msg(U, "/subs"))             # не админ
    assert not fake.texts(U)


async def test_csv_safe_neutralizes_formulas():
    from bot.broadcast import _csv_safe
    assert _csv_safe("=HYPERLINK(\"x\")") == "'=HYPERLINK(\"x\")"
    assert _csv_safe("+7") == "'+7" and _csv_safe("@a") == "'@a" and _csv_safe("-1") == "'-1"
    assert _csv_safe("Александр") == "Александр" and _csv_safe("") == ""


async def test_branding_sets_all_languages(tg):
    from aiogram.methods import SetMyDescription, SetMyName, SetMyShortDescription
    from bot.branding import BRAND, apply_branding
    dp, bot, fake, _ = tg
    fake.calls.clear()
    await apply_branding(bot)
    names = {c.language_code: c.name for c in fake.of(SetMyName)}
    assert names[None].startswith("Kai Tara") and names["ru"].startswith("Кай Тара")
    assert set(names) == {None, "ru", "en", "fr", "es", "de", "it"}
    assert len(fake.of(SetMyShortDescription)) == len(fake.of(SetMyDescription)) == len(BRAND)


async def test_promo_makes_everything_free(tg, repo):
    from datetime import date
    from bot.broadcast import send_daily
    dp, bot, fake, cfg = tg
    await register(dp, bot)
    await repo.pool.execute("UPDATE users SET premium_until = NULL WHERE tg_id = $1", U)
    cfg.free_until = date(2099, 12, 31)
    fake.calls.clear()
    for cmd in ("/personal", "/calendar", "/today"):
        await dp.feed_update(bot, msg(U, cmd))
    texts = fake.texts(U)
    assert not any(t.startswith("🔒") for t in texts)
    assert "Хорошо для" in texts[-1]
    await dp.feed_update(bot, msg(U, "/premium"))
    assert "бесплатны для всех" in fake.texts(U)[-1]
    cfg.daily_hour = 0
    assert await send_daily(bot, repo, cfg) == 1
    cfg.free_until = date(2000, 1, 1)                        # промо закончилось
    fake.calls.clear()
    await dp.feed_update(bot, msg(U, "/calendar"))
    assert fake.texts(U)[-1].startswith("🔒")


async def test_free_mode_unlocks_everything_without_payment_buttons(tg, repo):
    from aiogram.methods import SendInvoice
    from bot.payments import Paywall
    dp, bot, fake, cfg = tg
    cfg.free_mode = True
    await Paywall.init(bot, cfg)
    assert Paywall.links == {}
    await register(dp, bot)
    await repo.pool.execute("UPDATE users SET premium_until = NULL WHERE tg_id = $1", U)
    assert any("сейчас бесплатны" in x for x in fake.texts(U))
    fake.calls.clear()
    for cmd in ("/personal", "/calendar", "/compat", "/premium"):
        await dp.feed_update(bot, msg(U, cmd))
    texts = fake.texts(U)
    assert not any(x.startswith("🔒") for x in texts)
    assert any("бесплатны для всех" in x for x in texts)
    buttons = [b for c in fake.of(SendMessage) if c.reply_markup and hasattr(c.reply_markup, "inline_keyboard")
               for row in c.reply_markup.inline_keyboard for b in row]
    assert not any("⭐" in b.text for b in buttons) and not fake.of(SendInvoice)


async def test_source_command(tg, repo):
    dp, bot, fake, cfg = tg
    await dp.feed_update(bot, msg(U, "/source"))
    assert "AGPL-3.0" in fake.texts(U)[-1]
    cfg.source_url = "https://github.com/example/kai-tara"
    await dp.feed_update(bot, msg(U, "/source"))
    assert "github.com/example/kai-tara" in fake.texts(U)[-1]
