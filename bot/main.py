"""Запуск: python -m bot.main"""
import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from . import config, glossary
from .branding import apply_branding
from .i18n import t
from .lang import LangMiddleware
from .storage import TTLMemoryStorage
from .broadcast import scheduler, setup_admin
from .db import Repo
from .features import router as features_router
from .handlers import router
from .payments import Paywall, router as payments_router
from .report_flow import router as report_router
from .transits_handlers import router as transits_router
from .why import router as why_router
from .period_view import router as period_router
from .ics import router as ics_router
from .month_pdf import router as pdf30_router
from .varsha import router as varsha_router

log = logging.getLogger("main")
MIGRATIONS = Path(__file__).resolve().parent.parent / "migrations"
COMMANDS = ["forecast", "today", "week", "month", "personal", "compat", "calendar", "transits", "ics", "pdf30", "chart", "varsha", "glossary", "premium", "me",
            "settings", "help"]


async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    cfg = config.load()
    repo = await Repo.create(cfg.dsn, cfg.fernet_key)
    applied = await repo.migrate(str(MIGRATIONS))
    if applied:
        log.info("применены миграции: %s", ", ".join(applied))
    bot = Bot(cfg.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    glossary.BOT_USERNAME = (await bot.me()).username
    await Paywall.init(bot, cfg)
    asyncio.create_task(apply_branding(bot))
    storage = TTLMemoryStorage()
    dp = Dispatcher(storage=storage)
    dp["repo"] = repo
    dp["cfg"] = cfg
    dp.update.outer_middleware(LangMiddleware())
    dp.include_router(setup_admin(cfg.admin_ids))
    dp.include_router(payments_router)      # платежи раньше всех: successful_payment не должен уйти в FSM
    dp.include_router(router)
    dp.include_router(features_router)
    dp.include_router(transits_router)
    dp.include_router(report_router)
    dp.include_router(why_router)
    dp.include_router(period_router)
    dp.include_router(ics_router)
    dp.include_router(pdf30_router)
    dp.include_router(varsha_router)
    for code, lang in ((None, "en"), ("ru", "ru")):     # по умолчанию английский, для ru — русский
        await bot.set_my_commands([BotCommand(command=c, description=t(lang, f"cmd_{c}")) for c in COMMANDS],
                                  language_code=code)
    asyncio.create_task(scheduler(bot, repo, cfg))
    asyncio.create_task(storage.sweeper())
    from jyotish import geo
    asyncio.create_task(asyncio.to_thread(geo.index))      # индекс городов грузим заранее (~1 с)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
