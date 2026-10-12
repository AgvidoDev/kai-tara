"""Фикстуры интеграционных тестов: встроенный PostgreSQL (pgserver) и бот с подменённым Telegram API."""
from __future__ import annotations

import itertools
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
import pytest_asyncio

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def pg_uri():
    uri = os.environ.get("TEST_DATABASE_URL")
    if uri:
        yield uri
        return
    pgserver = pytest.importorskip("pgserver")
    tmp = tempfile.mkdtemp(prefix="astro_pg_")
    srv = pgserver.get_server(tmp, cleanup_mode="stop")
    srv.psql("CREATE DATABASE astro_test;")
    yield srv.get_uri("astro_test")


@pytest_asyncio.fixture
async def repo(pg_uri):
    from bot.db import Repo
    from cryptography.fernet import Fernet
    import asyncpg
    con = await asyncpg.connect(pg_uri)
    await con.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    await con.execute((ROOT / "schema.sql").read_text(encoding="utf-8"))
    await con.close()
    r = await Repo.create(pg_uri, Fernet.generate_key().decode())
    await r.migrate(str(ROOT / "migrations"))
    yield r
    await r.pool.close()


# ------------------------------------------------------------------ фейковый Telegram
class FakeSession:
    """Записывает все вызовы Bot API и возвращает правдоподобные ответы."""

    def __init__(self):
        from aiogram.client.session.base import BaseSession

        class _S(BaseSession):
            async def make_request(s, bot, method, timeout=None):
                return self._respond(method)

            async def stream_content(s, *a, **kw):
                raise NotImplementedError

            async def close(s):
                pass

        self.session = _S()
        self.calls: list = []
        self._ids = itertools.count(1000)

    def _respond(self, method):
        from aiogram.methods import CreateInvoiceLink, GetMe
        from aiogram.types import Chat, Message, User
        self.calls.append(method)
        if isinstance(method, GetMe):
            return User(id=1, is_bot=True, first_name="astro", username="astro_test_bot")
        if isinstance(method, CreateInvoiceLink):
            return "https://t.me/$invoice_test"
        if type(method).__name__ in ("GetMyName", "GetMyShortDescription", "GetMyDescription"):
            from types import SimpleNamespace
            return SimpleNamespace(name="old", short_description="old", description="old")
        if type(method).__name__ == "GetChat":
            from types import SimpleNamespace
            return SimpleNamespace(first_name=f"Name{method.chat_id}", last_name=None,
                                   username=f"user{method.chat_id}")
        ret = getattr(method, "__returning__", None)
        if ret is Message or getattr(ret, "__name__", "") == "Message":
            chat_id = getattr(method, "chat_id", 1) or 1
            return Message(message_id=next(self._ids), date=datetime.now(timezone.utc),
                           chat=Chat(id=chat_id, type="private"),
                           text=getattr(method, "text", None) or "ok")
        return True

    def texts(self, chat_id: int | None = None) -> list[str]:
        out = []
        for c in self.calls:
            t = getattr(c, "text", None) or getattr(c, "title", None)
            if t and (chat_id is None or getattr(c, "chat_id", None) == chat_id):
                out.append(t)
        return out

    def of(self, cls):
        return [c for c in self.calls if isinstance(c, cls)]


@pytest_asyncio.fixture
async def tg(repo):
    """(dispatcher, bot, fake) — бот как в main.py, но без сети."""
    from aiogram import Bot, Dispatcher
    from aiogram.client.default import DefaultBotProperties
    from bot import glossary
    from bot.broadcast import setup_admin
    from bot.config import Config
    from bot.features import router as features_router
    from bot.handlers import router
    from bot.payments import Paywall, router as payments_router
    from bot.report_flow import router as report_router
    from bot.transits_handlers import router as transits_router
    from bot.why import router as why_router
    from bot.period_view import router as period_router
    from bot.ics import router as ics_router
    from bot.month_pdf import router as pdf30_router

    fake = FakeSession()
    bot = Bot("42:" + "A" * 35, session=fake.session, default=DefaultBotProperties(parse_mode="HTML"))
    cfg = Config(bot_token="x", dsn="", fernet_key="", admin_ids={999})
    glossary.BOT_USERNAME = "astro_test_bot"
    await Paywall.init(bot, cfg)
    from bot.storage import TTLMemoryStorage
    dp = Dispatcher(storage=TTLMemoryStorage())
    dp["repo"] = repo
    dp["cfg"] = cfg
    from bot.lang import LangMiddleware, _cache
    _cache.clear()
    dp.update.outer_middleware(LangMiddleware())
    for r in (setup_admin(cfg.admin_ids), payments_router, router, features_router, transits_router, report_router, why_router, period_router, ics_router, pdf30_router):
        r._parent_router = None   # роутеры — модульные синглтоны, отвязываем от прошлого теста
        dp.include_router(r)
    yield dp, bot, fake, cfg
    glossary.BOT_USERNAME = None


_upd = itertools.count(1)


def msg(user_id: int, text: str = None, lang: str = "ru", **kw):
    from aiogram.types import Chat, Message, Update, User
    m = Message(message_id=next(_upd), date=datetime.now(timezone.utc),
                chat=Chat(id=user_id, type="private"),
                from_user=User(id=user_id, is_bot=False, first_name="U", username=f"u{user_id}", language_code=lang),
                text=text, **kw)
    return Update(update_id=next(_upd), message=m)


def cb(user_id: int, data: str, text: str = "msg", lang: str = "ru"):
    from aiogram.types import CallbackQuery, Chat, Message, Update, User
    u = User(id=user_id, is_bot=False, first_name="U", language_code=lang)
    m = Message(message_id=next(_upd), date=datetime.now(timezone.utc), chat=Chat(id=user_id, type="private"),
                from_user=User(id=1, is_bot=True, first_name="astro"), text=text)
    return Update(update_id=next(_upd), callback_query=CallbackQuery(
        id=str(next(_upd)), from_user=u, chat_instance="ci", message=m, data=data))
