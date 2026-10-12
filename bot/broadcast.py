"""Автоматическая рассылка прогнозов в момент новолуния/полнолуния + админ-команды."""
from __future__ import annotations

import asyncio
import csv
import io
import logging
from datetime import datetime, timezone
from html import escape
from zoneinfo import ZoneInfo

from aiogram import Bot, Router
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, InlineKeyboardMarkup, Message

from jyotish.core import from_jd, to_jd
from jyotish.events import lunations

from .astro_service import daily_personal, lunation_facts, render_daily, render_sign, settings_for
from .config import Config
from .db import Repo
from .glossary import linkify, terms_button

log = logging.getLogger("broadcast")
admin_router = Router()


async def prepare_run(repo: Repo, lun, city_key: str) -> tuple[int, bool, dict]:
    s = settings_for(city_key)
    facts = await asyncio.to_thread(lunation_facts, lun, s)
    run_id, is_new = await repo.save_run(
        lun.kind, from_jd(lun.jd, "UTC"), datetime.fromisoformat(facts["event"]["period_until"]),
        city_key, s.ayanamsha, s.true_node, facts)
    if is_new:  # тексты для всех 12 знаков × 3 режима — пригодятся сайту и YouTube
        for mode in ("moon", "sun_sid", "sun_trop"):
            for sign in range(12):
                await repo.save_text(run_id, mode, sign, "telegram", render_sign(facts, mode, sign))
    return run_id, is_new, facts


async def safe_send(bot: Bot, tg_id: int, html: str, lang: str = "ru") -> bool:
    """Отправка с термин-ссылками; переживает лимиты и блокировку бота."""
    text = linkify(html, lang=lang)
    kbd = InlineKeyboardMarkup(inline_keyboard=[[terms_button(lang)]])
    try:
        await bot.send_message(tg_id, text, reply_markup=kbd)
        return True
    except TelegramRetryAfter as e:
        await asyncio.sleep(e.retry_after)
        await bot.send_message(tg_id, text, reply_markup=kbd)
        return True
    except TelegramForbiddenError:
        log.info("пользователь %s заблокировал бота", tg_id)
        return False


async def safe_send_raw(bot: Bot, tg_id: int, text: str, kbd: InlineKeyboardMarkup | None = None) -> bool:
    """Отправка готового текста (уже со ссылками) с клавиатурой."""
    try:
        await bot.send_message(tg_id, text, reply_markup=kbd)
        return True
    except TelegramRetryAfter as e:
        await asyncio.sleep(e.retry_after)
        await bot.send_message(tg_id, text, reply_markup=kbd)
        return True
    except TelegramForbiddenError:
        log.info("пользователь %s заблокировал бота", tg_id)
        return False


async def send_to_subscribers(bot: Bot, repo: Repo, facts: dict, city_key: str) -> int:
    sent = 0
    for u in await repo.subscribers(city_key):
        sign = {"moon": u["moon_rashi"], "sun_sid": u["sun_sid_rashi"], "sun_trop": u["sun_trop_sign"]}[u["sign_mode"]]
        if sign is None:
            continue
        lang = u["lang"] or "ru"
        sent += await safe_send(bot, u["tg_id"], render_sign(facts, u["sign_mode"], sign, lang, city_key), lang)
        await asyncio.sleep(0.05)  # ~20 сообщений/сек, ниже лимита Telegram
    return sent


async def send_daily(bot: Bot, repo: Repo, cfg: Config) -> int:
    """Утренний прогноз «Сегодня» премиум-пользователям после DAILY_HOUR по их времени."""
    sent = 0
    for u in await repo.daily_candidates(cfg.promo_active):
        now = datetime.now(ZoneInfo(u["tz"]))
        if now.hour < cfg.daily_hour:
            continue
        if not await repo.mark_daily_sent(u["id"], now.date()):
            continue  # сегодня уже отправляли
        try:
            p = await asyncio.to_thread(daily_personal, now.date(), settings_for(u["city_key"]),
                                        u["moon_rashi"], u["moon_nakshatra"])
            lang = u["lang"] or "ru"
            sent += await safe_send(bot, u["tg_id"], render_daily(p, True, lang, u["city_key"]), lang)
        except Exception:
            log.exception("утренний прогноз для %s", u["tg_id"])
        await asyncio.sleep(0.05)
    return sent


async def check_lunations(bot: Bot, repo: Repo, window_hours: float) -> None:
    now = to_jd(datetime.now(timezone.utc))
    recent = lunations(now - window_hours / 24, now)
    for lun in recent:
        for city in await repo.cities_in_use():
            _, is_new, facts = await prepare_run(repo, lun, city)
            if is_new:
                n = await send_to_subscribers(bot, repo, facts, city)
                log.info("лунация %s, %s: отправлено %d", lun.kind, city, n)


async def scheduler(bot: Bot, repo: Repo, cfg: Config) -> None:
    while True:
        try:
            await check_lunations(bot, repo, cfg.send_window_hours)
        except Exception:
            log.exception("ошибка планировщика лунаций")
        try:
            from .transits_handlers import send_transit_pushes
            n = await send_transit_pushes(bot, repo)
            if n:
                log.info("пуши о транзитах: отправлено %d", n)
        except Exception:
            log.exception("ошибка пушей о транзитах")
        try:
            n = await send_daily(bot, repo, cfg)
            if n:
                log.info("утренний прогноз: отправлено %d", n)
        except Exception:
            log.exception("ошибка утренней рассылки")
        await asyncio.sleep(cfg.check_interval_sec)


# ------------------------------------------------------------------ админ
async def _names(bot: Bot, ids: list[int], limit: int = 300) -> dict[int, tuple[str, str]]:
    """Имя и username из Telegram на лету (в базу не пишем). Больше limit — только ID."""
    out = {}
    for tg_id in ids[:limit]:
        try:
            ch = await bot.get_chat(tg_id)
            name = " ".join(x for x in (ch.first_name, ch.last_name) if x)
            out[tg_id] = (name, ch.username or "")
        except Exception:
            out[tg_id] = ("", "")
        await asyncio.sleep(0.03)
    return out


def _csv_safe(v: str) -> str:
    """Имя задаёт пользователь: «=…», «+…», «-…», «@…» Excel выполнит как формулу — экранируем."""
    return "'" + v if v and v[0] in "=+-@\t\r" else v


def _chunks(lines: list[str], limit: int = 3900) -> list[str]:
    out, cur = [], ""
    for ln in lines:
        if len(cur) + len(ln) + 1 > limit:
            out.append(cur)
            cur = ""
        cur += ln + "\n"
    if cur.strip():
        out.append(cur)
    return out


def setup_admin(admin_ids: set[int]) -> Router:
    from aiogram import F
    admin_router.message.filter(F.from_user.id.in_(admin_ids))

    @admin_router.message(Command("preview"))
    async def preview(m: Message, repo: Repo):
        """/preview [moon|sun_sid|sun_trop] — все 12 знаков текущего лунного месяца."""
        from .astro_service import current_new_moon
        parts = (m.text or "").split()
        mode = parts[1] if len(parts) > 1 else "sun_trop"
        s = settings_for("moscow")
        lun = await asyncio.to_thread(current_new_moon, datetime.now(timezone.utc), s)
        facts = await asyncio.to_thread(lunation_facts, lun, s)
        for sign in range(12):
            await m.answer(linkify(render_sign(facts, mode, sign)))
            await asyncio.sleep(0.1)

    @admin_router.message(Command("stats"))
    async def stats(m: Message, repo: Repo, cfg: Config):
        r = await repo.pool.fetchrow(
            """SELECT count(*) users, count(b.user_id) with_birth,
                      count(*) FILTER (WHERE b.time_known) with_time
               FROM users u LEFT JOIN profiles b ON b.user_id = u.id""")
        modes = await repo.pool.fetch("SELECT sign_mode, count(*) FROM users GROUP BY 1")
        prem = await repo.pool.fetchrow(
            """SELECT count(*) FILTER (WHERE premium_until > now()) active,
                      count(*) FILTER (WHERE sub_charge_id IS NOT NULL AND premium_until > now()) paying,
                      count(*) FILTER (WHERE referred_by IS NOT NULL AND ref_rewarded) referred
               FROM users""")
        rev = await repo.pool.fetchrow(
            """SELECT coalesce(sum(stars) FILTER (WHERE created_at > now() - interval '30 days'), 0) m30,
                      coalesce(sum(stars), 0) total, count(*) n
               FROM payments WHERE refunded_at IS NULL""")
        await m.answer(f"Пользователей: {r['users']}\nС данными рождения: {r['with_birth']}\n"
                       f"Со временем: {r['with_time']}\n" +
                       "\n".join(f"{x['sign_mode']}: {x['count']}" for x in modes) +
                       f"\n\n💎 Премиум активен: {prem['active']} (платящих: {prem['paying']})\n"
                       f"Приглашено друзьями: {prem['referred']}\n"
                       f"⭐ За 30 дней: {rev['m30']}, всего: {rev['total']} ({rev['n']} платежей)" +
                       ("\n\n🎁 Бесплатный режим: оплата выключена (FREE_MODE)" if cfg.free_mode else
                        f"\n\n🎁 Промо: Премиум бесплатен всем до {cfg.free_until:%d.%m.%Y}" if cfg.promo_active else ""))

    @admin_router.message(Command("grant"))
    async def grant(m: Message, repo: Repo):
        """/grant <tg_id> <дни> — подарить Премиум."""
        parts = (m.text or "").split()
        if len(parts) != 3 or not parts[1].isdigit() or not parts[2].lstrip("-").isdigit():
            return await m.answer("Формат: /grant <tg_id> <дни>")
        until = await repo.extend_premium(int(parts[1]), int(parts[2]))
        await m.answer(f"Премиум до {until:%d.%m.%Y}" if until else "Пользователь не найден")

    @admin_router.message(Command("refund"))
    async def refund(m: Message, repo: Repo, bot: Bot):
        """/refund <tg_id> <charge_id> — вернуть звёзды."""
        parts = (m.text or "").split()
        if len(parts) != 3 or not parts[1].isdigit():
            return await m.answer("Формат: /refund <tg_id> <charge_id>")
        tg_id, charge = int(parts[1]), parts[2]
        try:
            await bot.refund_star_payment(tg_id, charge)
        except Exception as e:
            return await m.answer(f"Telegram отклонил возврат: {e}")
        row = await repo.mark_refunded(charge)
        if row and row["product"] == "premium_sub":
            await repo.pool.execute(
                "UPDATE users SET premium_until = now(), sub_canceled = true WHERE tg_id = $1", tg_id)
        await m.answer("Возврат выполнен." + ("" if row else " (платёж не найден в базе)"))

    @admin_router.message(Command("subs"))
    async def subs(m: Message, repo: Repo, bot: Bot):
        """/subs — платящие и пробные; /subs paid; /subs all — все пользователи; /subs csv — файлом."""
        arg = ((m.text or "").split() + [""])[1].lower()
        rows = await repo.pool.fetch(
            """SELECT u.tg_id, u.created_at, u.premium_until, u.sub_charge_id IS NOT NULL AS paying,
                      u.sub_canceled, b.user_id IS NOT NULL AS has_birth, coalesce(p.stars, 0) AS stars
               FROM users u
               LEFT JOIN profiles b ON b.user_id = u.id
               LEFT JOIN (SELECT tg_id, sum(stars) stars FROM payments
                          WHERE refunded_at IS NULL GROUP BY tg_id) p ON p.tg_id = u.tg_id
               WHERE u.tg_id IS NOT NULL
               ORDER BY u.premium_until DESC NULLS LAST, u.created_at DESC""")
        now = datetime.now(timezone.utc)
        active = [r for r in rows if r["premium_until"] and r["premium_until"] > now]
        paying = [r for r in active if r["paying"]]
        free = [r for r in active if not r["paying"]]
        names = await _names(bot, [r["tg_id"] for r in (rows if arg in ("all", "csv") else active)])

        if arg == "csv":
            buf = io.StringIO()
            w = csv.writer(buf, delimiter=";")
            w.writerow(["tg_id", "имя", "username", "регистрация", "данные рождения", "премиум до",
                        "подписка", "автопродление", "звёзд оплачено"])
            for r in rows:
                n = names.get(r["tg_id"], ("", ""))
                w.writerow([r["tg_id"], _csv_safe(n[0]), _csv_safe(n[1]), f"{r['created_at']:%Y-%m-%d}", "да" if r["has_birth"] else "нет",
                            f"{r['premium_until']:%Y-%m-%d}" if r["premium_until"] else "",
                            "да" if r["paying"] else "нет",
                            "" if not r["paying"] else ("выкл" if r["sub_canceled"] else "вкл"), r["stars"]])
            data = buf.getvalue().encode("utf-8-sig")       # BOM — чтобы Excel открыл кириллицу
            return await m.answer_document(BufferedInputFile(data, f"astro_users_{now:%Y%m%d}.csv"),
                                           caption=f"Пользователей: {len(rows)}")

        def line(r) -> str:
            name, uname = names.get(r["tg_id"], ("", ""))
            who = " ".join(x for x in (escape(name), f"@{escape(uname)}" if uname else "") if x)
            until = f" — до {r['premium_until']:%d.%m.%Y}" if r["premium_until"] and r["premium_until"] > now else ""
            renew = (" ⟳" if not r["sub_canceled"] else " ⏹") if r["paying"] and until else ""
            stars = f" {r['stars']}⭐" if r["stars"] else ""
            return f"• <code>{r['tg_id']}</code> {who}{until}{renew}{stars}"

        if arg == "all":
            out = [f"👥 <b>Все пользователи: {len(rows)}</b> (💎 — Премиум, 📝 — ввёл данные рождения)", ""]
            out += [("💎" if r in active else "  ") + ("📝 " if r["has_birth"] else " ") + line(r)[2:]
                    + f" · с {r['created_at']:%d.%m.%Y}" for r in rows]
        else:
            out = [f"💎 <b>Платящие: {len(paying)}</b>  (⟳ автопродление, ⏹ отменено)"]
            out += [line(r) for r in paying] or ["—"]
            if arg != "paid":
                out += ["", f"🎁 <b>Пробный период и подарки: {len(free)}</b>"]
                out += [line(r) for r in free] or ["—"]
            out += ["", "Все пользователи: /subs all · файлом: /subs csv"]
        for chunk in _chunks(out):
            await m.answer(chunk)

    @admin_router.message(Command("payments"))
    async def payments(m: Message, repo: Repo):
        rows = await repo.pool.fetch(
            "SELECT tg_id, charge_id, product, stars, created_at, refunded_at FROM payments ORDER BY id DESC LIMIT 15")
        if not rows:
            return await m.answer("Платежей пока нет.")
        await m.answer("\n".join(
            f"{r['created_at']:%d.%m %H:%M} {r['tg_id']} {r['product']} {r['stars']}⭐"
            f"{' ↩' if r['refunded_at'] else ''}\n<code>{r['charge_id']}</code>" for r in rows))

    return admin_router
