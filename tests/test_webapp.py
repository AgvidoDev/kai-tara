"""Mini App: проверка подписи initData и JSON API."""
import hashlib
import hmac
import json
import time
from datetime import date
from urllib.parse import urlencode

import pytest
from aiohttp.test_utils import TestClient, TestServer

from bot.webapp import make_app, verify_init_data
from tests.test_bot_flow import U, register

TOKEN = "42:" + "A" * 35


def sign(user_id: int, token: str = TOKEN, auth_date: int | None = None, lang: str = "ru") -> str:
    data = {"auth_date": str(auth_date or int(time.time())), "query_id": "AAE",
            "user": json.dumps({"id": user_id, "first_name": "X", "language_code": lang})}
    check = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    data["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return urlencode(data)


def test_signature_ok_and_tampered():
    good = sign(7)
    assert verify_init_data(good, TOKEN)["id"] == 7
    assert verify_init_data(good, "1:" + "B" * 35) is None                    # другой бот
    assert verify_init_data(good.replace("%22id%22%3A+7", "%22id%22%3A+8"), TOKEN) is None
    assert verify_init_data(sign(7, auth_date=int(time.time()) - 2 * 86400), TOKEN) is None
    assert verify_init_data("", TOKEN) is None and verify_init_data("hash=zz", TOKEN) is None


@pytest.fixture
async def client(tg, repo):
    dp, bot, fake, cfg = tg
    cfg.bot_token = TOKEN
    c = TestClient(TestServer(make_app(repo, cfg)))
    await c.start_server()
    yield c, dp, bot, cfg, repo
    await c.close()


def H(uid: int = U) -> dict:
    return {"Authorization": "tma " + sign(uid)}


@pytest.mark.asyncio
async def test_api_requires_signature(client):
    c, *_ = client
    assert (await c.get("/api/me")).status == 401
    assert (await c.get("/api/me", headers={"Authorization": "tma bad"})).status == 401
    r = await c.get("/")
    assert r.status == 200 and "Content-Security-Policy" in r.headers


@pytest.mark.asyncio
async def test_me_day_period_family(client):
    c, dp, bot, cfg, repo = client
    r = await c.get("/api/me", headers=H())
    assert (await r.json()) == {"lang": "ru", "has_birth": False}
    assert (await c.get("/api/day", headers=H())).status == 409
    await register(dp, bot)
    cfg.free_until = date(2099, 1, 1)
    me = await (await c.get("/api/me", headers=H())).json()
    assert me["has_birth"] and me["moon"] and me["nakshatra"] and me["dasha"]["maha"]
    day = await (await c.get("/api/day", headers=H())).json()
    assert day["premium"] and day["do"] and day["sky"] and day["tone_text"]
    day2 = await (await c.get("/api/day?date=2026-01-01", headers=H())).json()
    assert day2["date"] == "2026-01-01"
    assert (await c.get("/api/day?date=xx", headers=H())).status == 400
    week = await (await c.get("/api/period?days=7", headers=H())).json()
    assert len(week["days"]) == 7
    assert len((await (await c.get("/api/period?days=30", headers=H())).json())["days"]) == 30
    assert (await c.get("/api/period?days=99", headers=H())).status == 400
    assert (await (await c.get("/api/family", headers=H())).json()) == {"items": []}
    assert (await c.get("/api/transits", headers=H())).status == 200


@pytest.mark.asyncio
async def test_relative_access_is_private(client):
    from jyotish.profile import compute
    from datetime import datetime
    c, dp, bot, cfg, repo = client
    await register(dp, bot)
    await register(dp, bot, uid=U + 1)
    cfg.free_until = date(2099, 1, 1)
    rid = await repo.add_relative(U, "Мама", compute(datetime(1955, 2, 3, 8, 15), 59.9, 30.3, "Europe/Moscow", True))
    day = await (await c.get(f"/api/day?rel={rid}", headers=H())).json()
    assert day["who"] == "Мама"
    assert (await c.get(f"/api/day?rel={rid}", headers=H(U + 1))).status == 404       # чужой профиль
    assert (await c.get("/api/day?rel=abc", headers=H())).status == 400


@pytest.mark.asyncio
async def test_period_needs_premium(client):
    c, dp, bot, cfg, repo = client
    await register(dp, bot)
    await repo.pool.execute("UPDATE users SET premium_until = now() - interval '1 day' WHERE tg_id = $1", U)
    assert (await c.get("/api/period?days=7", headers=H())).status == 402
    day = await (await c.get("/api/day", headers=H())).json()
    assert not day["premium"] and "do" not in day
