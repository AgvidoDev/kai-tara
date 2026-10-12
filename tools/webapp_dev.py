"""Локальный просмотр Mini App без Telegram: встроенный PostgreSQL, тестовый пользователь, порт 8111.

Запуск: python tools/webapp_dev.py — печатает initData для подстановки в window.Telegram.WebApp.
"""
import asyncio
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


async def main():
    import asyncpg
    import pgserver
    from aiohttp import web

    from bot.config import Config
    from bot.db import Repo
    from bot.webapp import make_app
    from jyotish.profile import compute
    from tests.test_webapp import sign

    srv = pgserver.get_server(tempfile.mkdtemp(prefix="astro_dev_"), cleanup_mode="stop")
    srv.psql("CREATE DATABASE astro_dev;")
    uri = srv.get_uri("astro_dev")
    con = await asyncpg.connect(uri)
    await con.execute((ROOT / "schema.sql").read_text(encoding="utf-8"))
    await con.close()
    repo = await Repo.create(uri)
    await repo.migrate(str(ROOT / "migrations"))
    uid = 100
    await repo.ensure_user(uid)
    await repo.set_lang(uid, "ru")
    await repo.set_city(uid, "spb", "Europe/Moscow")
    await repo.save_profile(uid, compute(datetime(1980, 5, 14, 6, 30), 59.93, 30.33, "Europe/Moscow", True))
    await repo.add_relative(uid, "Мама", compute(datetime(1955, 2, 3, 8, 15), 59.9, 30.3, "Europe/Moscow", True))
    cfg = Config(bot_token="42:" + "A" * 35, dsn=uri, fernet_key="", free_mode=True, free_until=date(2099, 1, 1))
    runner = web.AppRunner(make_app(repo, cfg))
    await runner.setup()
    await web.TCPSite(runner, "127.0.0.1", 8111).start()
    print("INITDATA=" + sign(uid), flush=True)
    await asyncio.Event().wait()


asyncio.run(main())
