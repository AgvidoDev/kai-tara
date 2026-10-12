"""Премиум и оплата через Telegram Stars (XTR): подписка, разовые покупки, возвраты."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice,
                           Message, PreCheckoutQuery)

from jyotish.texts import LANGS, fmt_date

from . import keyboards as kb
from .config import Config
from .db import Repo
from .i18n import t

log = logging.getLogger("payments")
router = Router()

SUB_PERIOD = 30 * 24 * 3600          # Telegram принимает только 30 дней
P_SUB = "premium_sub"
P_COMPAT = "compat"
P_REPORT = "report"


class Paywall:
    """Ссылки на подписку создаются один раз при старте (многоразовые), по одной на язык."""
    links: dict[str, str] = {}

    @classmethod
    async def init(cls, bot: Bot, cfg: Config) -> None:
        if cfg.free_mode:              # бесплатный режим: счета не создаём, кнопок оплаты нет нигде
            cls.links = {}
            return
        for lang in LANGS:
            try:
                cls.links[lang] = await bot.create_invoice_link(
                    title=t(lang, "inv_sub_title"), description=t(lang, "inv_sub_desc"),
                    payload=P_SUB, currency="XTR",
                    prices=[LabeledPrice(label=t(lang, "inv_sub_label"), amount=cfg.price_premium)],
                    subscription_period=SUB_PERIOD)
            except Exception:
                log.exception("не удалось создать ссылку на подписку (%s) — кнопка оплаты скрыта", lang)

    @classmethod
    def link(cls, lang: str) -> str | None:
        return cls.links.get(lang) or cls.links.get("ru")


def is_premium(u, cfg: Config) -> bool:
    return bool(u) and (cfg.promo_active or u["tg_id"] in cfg.admin_ids or Repo.premium_active(u))


def promo_line(cfg: Config, lang: str = "ru") -> str:
    if cfg.free_mode:
        return t(lang, "free_line")
    return t(lang, "promo_line", until=fmt_date(cfg.free_until, lang))


def paywall_kb(cfg: Config, with_compat: bool = False, lang: str = "ru") -> InlineKeyboardMarkup:
    rows = []
    if Paywall.link(lang):
        rows.append([InlineKeyboardButton(text=t(lang, "kb_buy_premium", price=cfg.price_premium),
                                          url=Paywall.link(lang))])
    if with_compat:
        rows.append([InlineKeyboardButton(text=t(lang, "kb_buy_compat", price=cfg.price_compat),
                                          callback_data="buy:compat")])
    rows.append([InlineKeyboardButton(text=t(lang, "kb_ref"), callback_data="ref:link")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def send_paywall(m: Message, cfg: Config, feature: str, with_compat: bool = False, lang: str = "ru") -> None:
    await m.answer(t(lang, "paywall", feature=feature, features=t(lang, "premium_features")),
                   reply_markup=paywall_kb(cfg, with_compat, lang))


def _until(dt: datetime | None, lang: str = "ru") -> str:
    return fmt_date(dt.astimezone(timezone(timedelta(hours=3))), lang) if dt else "—"


# ------------------------------------------------------------------ экран «Премиум»
@router.message(Command("premium"))
@router.message(F.text.in_(kb.BTN_PREMIUM))
async def premium_screen(m: Message, repo: Repo, cfg: Config, lang: str):
    await repo.ensure_user(m.from_user.id)
    u = await repo.get_user(m.from_user.id)
    lines = [t(lang, "premium_title"), "", t(lang, "premium_features"), ""]
    rows = []
    if cfg.promo_active and not Repo.premium_active(u):
        lines += [promo_line(cfg, lang), t(lang, "promo_no_pay")]
        kbd = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
            text=t(lang, "kb_invite"), callback_data="ref:link")]])
        return await m.answer("\n".join(lines + ["", t(lang, "terms_link")]), reply_markup=kbd)
    if is_premium(u, cfg):
        if m.from_user.id in cfg.admin_ids and not Repo.premium_active(u):
            lines.append(t(lang, "status_admin"))
        else:
            lines.append(t(lang, "status_active", until=_until(u["premium_until"], lang)))
            if u["sub_charge_id"] and not u["sub_canceled"]:
                lines.append(t(lang, "renew_on"))
                rows.append([InlineKeyboardButton(text=t(lang, "kb_sub_cancel"), callback_data="sub:cancel")])
            elif u["sub_charge_id"]:
                lines.append(t(lang, "renew_off"))
                rows.append([InlineKeyboardButton(text=t(lang, "kb_sub_resume"), callback_data="sub:resume")])
    else:
        lines.append(t(lang, "price_line", price=cfg.price_premium))
    if u["compat_credits"]:
        lines.append(t(lang, "credits", n=u["compat_credits"]))
    if u["report_credits"]:
        lines.append(t(lang, "report_credits", n=u["report_credits"]))
    lines += ["", t(lang, "invite_line", days=cfg.ref_bonus_days), t(lang, "terms_link")]
    kbd = paywall_kb(cfg, with_compat=True, lang=lang)
    if is_premium(u, cfg) and Paywall.link(lang):
        kbd.inline_keyboard = kbd.inline_keyboard[1:]   # кнопка подписки уже не нужна
    kbd.inline_keyboard = rows + kbd.inline_keyboard
    await m.answer("\n".join(lines), reply_markup=kbd)


@router.callback_query(F.data == "ref:link")
async def ref_link(c: CallbackQuery, repo: Repo, cfg: Config, bot: Bot, lang: str):
    me = await bot.me()
    link = f"https://t.me/{me.username}?start=ref_{c.from_user.id}"
    n = await repo.referrals_count(c.from_user.id)
    await c.message.answer(t(lang, "ref_text", link=link, days=cfg.ref_bonus_days, n=n))
    await c.answer()


@router.callback_query(F.data.in_({"sub:cancel", "sub:resume"}))
async def sub_toggle(c: CallbackQuery, repo: Repo, bot: Bot, lang: str):
    u = await repo.get_user(c.from_user.id)
    if not u or not u["sub_charge_id"]:
        return await c.answer(t(lang, "sub_not_found"), show_alert=True)
    cancel = c.data == "sub:cancel"
    try:
        await bot.edit_user_star_subscription(c.from_user.id, u["sub_charge_id"], is_canceled=cancel)
    except Exception:
        log.exception("edit_user_star_subscription")
        return await c.answer(t(lang, "sub_error"), show_alert=True)
    await repo.set_sub_canceled(c.from_user.id, cancel)
    await c.message.answer(t(lang, "sub_cancelled", until=_until(u["premium_until"], lang)) if cancel
                           else t(lang, "sub_resumed"))
    await c.answer()


# ------------------------------------------------------------------ покупки
@router.callback_query(F.data == "buy:compat")
async def buy_compat(c: CallbackQuery, cfg: Config, lang: str):
    await c.message.answer_invoice(
        title=t(lang, "inv_compat_title"), description=t(lang, "inv_compat_desc"),
        payload=P_COMPAT, currency="XTR",
        prices=[LabeledPrice(label=t(lang, "inv_compat_label"), amount=cfg.price_compat)])
    await c.answer()


@router.pre_checkout_query()
async def pre_checkout(q: PreCheckoutQuery, cfg: Config, lang: str):
    expected = {P_SUB: cfg.price_premium, P_COMPAT: cfg.price_compat, P_REPORT: cfg.price_report}
    ok = q.currency == "XTR" and expected.get(q.invoice_payload) == q.total_amount
    await q.answer(ok=ok, error_message=None if ok else t(lang, "price_changed"))


@router.message(F.successful_payment)
async def paid(m: Message, repo: Repo, cfg: Config, lang: str, state: FSMContext):
    sp = m.successful_payment
    tg_id = m.from_user.id
    await repo.ensure_user(tg_id)
    product = sp.invoice_payload
    if not await repo.record_payment(tg_id, sp.telegram_payment_charge_id, product, sp.total_amount,
                                     bool(sp.is_recurring)):
        return  # повтор апдейта — уже обработан
    if product == P_SUB:
        until = (datetime.fromtimestamp(sp.subscription_expiration_date, timezone.utc)
                 if sp.subscription_expiration_date else datetime.now(timezone.utc) + timedelta(days=30))
        await repo.set_subscription(tg_id, sp.telegram_payment_charge_id, until)
        first = sp.is_first_recurring or not sp.is_recurring
        if first:
            await m.answer(t(lang, "paid_first", until=_until(until, lang), b1=t(lang, "btn_today"),
                             b2=t(lang, "btn_calendar"), b3=t(lang, "btn_compat")), reply_markup=kb.main_menu(lang))
        else:
            await m.answer(t(lang, "paid_renew", until=_until(until, lang)), reply_markup=kb.main_menu(lang))
    elif product == P_COMPAT:
        await repo.add_compat_credit(tg_id)
        await m.answer(t(lang, "paid_compat", btn=t(lang, "btn_compat")), reply_markup=kb.main_menu(lang))
    elif product == P_REPORT:
        from .report_flow import after_payment
        await repo.add_report_credit(tg_id)
        await after_payment(m, repo, state, lang)
    log.info("платёж %s: %s %s⭐", tg_id, product, sp.total_amount)


# ------------------------------------------------------------------ обязательные команды
@router.message(Command("terms"))
async def terms(m: Message, lang: str):
    await m.answer(t(lang, "terms"))


@router.message(Command("paysupport"))
async def paysupport(m: Message, cfg: Config, bot: Bot, lang: str):
    text = (m.text or "").partition(" ")[2].strip()
    if not text:
        return await m.answer(t(lang, "paysupport_usage"))
    for admin in cfg.admin_ids:
        try:
            await bot.send_message(admin, f"💬 /paysupport от {m.from_user.id} "
                                          f"(@{m.from_user.username or '—'}, {lang}):\n{text}")
        except Exception:
            log.exception("paysupport forward")
    await m.answer(t(lang, "paysupport_ok"))
