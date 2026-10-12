"""PDF-разбор натальной карты: временное хранение данных карты (только память бота) и выдача отчёта."""
from __future__ import annotations

import asyncio
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, Message

from .config import Config
from .db import Repo
from .i18n import t

router = Router()

TTL = 30 * 60                 # данные карты живут в памяти не дольше 30 минут
READY = "chart_ready"         # состояние FSM (MemoryStorage — в базу не попадает)
P_REPORT = "report"


_timers: dict[str, asyncio.Task] = {}


async def keep_chart(state: FSMContext, chart: dict) -> None:
    ts = time.time()
    await state.set_state(READY)
    await state.set_data({"chart": chart, "chart_ts": ts})
    # активное стирание: через TTL данные удаляются, даже если пользователь больше не придёт
    key = str(state.key)
    old = _timers.pop(key, None)
    if old:
        old.cancel()
    _timers[key] = asyncio.create_task(_expire(state, ts, key))


async def _expire(state: FSMContext, ts: float, key: str, delay: float | None = None) -> None:
    try:
        await asyncio.sleep(TTL if delay is None else delay)
        data = await state.get_data()
        if data.get("chart_ts") == ts:          # не трогаем, если с тех пор построена новая карта
            await state.clear()
    finally:
        if _timers.get(key) is asyncio.current_task():
            _timers.pop(key, None)


async def pending_chart(state: FSMContext) -> dict | None:
    data = await state.get_data()
    chart, ts = data.get("chart"), data.get("chart_ts", 0)
    if not chart:
        return None
    if time.time() - ts > TTL:
        await state.clear()
        return None
    return chart


def report_free(u, cfg: Config) -> bool:
    return bool(u) and (cfg.promo_active or u["tg_id"] in cfg.admin_ids)


def report_keyboard(u, cfg: Config, lang: str) -> InlineKeyboardMarkup:
    free = report_free(u, cfg) or (u and u["report_credits"] > 0)
    text = t(lang, "kb_report_free") if free else t(lang, "kb_report_paid", price=cfg.price_report)
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=text, callback_data="rep:get")]])


async def send_report(m: Message, state: FSMContext, chart: dict, lang: str) -> None:
    from jyotish.core import Location, Settings
    from jyotish.natal import build_chart
    from jyotish.report import analyze

    from .report_pdf import build_pdf

    await m.answer(t(lang, "report_making"))
    loc = Location(chart["place"], chart["lat"], chart["lon"], chart["tz"])
    zone = ZoneInfo(chart["tz"])
    birth = datetime.strptime(f"{chart['date']} {chart['time']}", "%Y-%m-%d %H:%M").replace(tzinfo=zone)

    def work() -> bytes:
        ch = build_chart(birth, loc, Settings(location=loc))
        r = analyze(ch, datetime.now(zone), chart["known"])
        return build_pdf(ch, r, lang, chart["place"])

    pdf = await asyncio.to_thread(work)
    await state.clear()                      # отчёт выдан — данные рождения стираются из памяти
    await m.answer_document(BufferedInputFile(pdf, "chart_reading.pdf" if lang == "en" else "razbor_karty.pdf"),
                            caption=t(lang, "report_caption"))


@router.callback_query(F.data == "rep:get")
async def report_get(c: CallbackQuery, repo: Repo, cfg: Config, state: FSMContext, lang: str):
    chart = await pending_chart(state)
    if not chart:
        await c.message.answer(t(lang, "report_expired"))
        return await c.answer()
    u = await repo.get_user(c.from_user.id)
    if report_free(u, cfg) or await repo.use_report_credit(c.from_user.id):
        await c.answer()
        return await send_report(c.message, state, chart, lang)
    await c.message.answer_invoice(
        title=t(lang, "inv_report_title"), description=t(lang, "inv_report_desc"), payload=P_REPORT,
        currency="XTR", prices=[LabeledPrice(label=t(lang, "inv_report_label"), amount=cfg.price_report)])
    await c.answer()


async def after_payment(m: Message, repo: Repo, state: FSMContext, lang: str) -> None:
    """Оплата прошла: если карта ещё в памяти — сразу отдаём отчёт, иначе кредит ждёт следующей карты."""
    chart = await pending_chart(state)
    if chart and await repo.use_report_credit(m.from_user.id):
        await send_report(m, state, chart, lang)
    else:
        await m.answer(t(lang, "report_pending"))
