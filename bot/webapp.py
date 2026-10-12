"""Telegram Mini App: веб-сервер (aiohttp) внутри процесса бота — статика и JSON API.

Авторизация — подпись initData от Telegram (HMAC-SHA256 с ключом из токена бота), без паролей и cookie.
Ответы — только простой текст: фронтенд вставляет его через textContent.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qsl
from zoneinfo import ZoneInfo

from aiohttp import web

from jyotish.core import city_name
from jyotish.daily import advice, describe_sky, reasons_text, special_text
from jyotish.texts import NAKSHATRA_NAME, PLANET, SIGN, WEEKDAY_SHORT, event_text, fmt_date

from .astro_service import daily_personal, settings_for
from .config import Config
from .db import Repo
from .i18n import detect
from .payments import is_premium

STATIC = Path(__file__).resolve().parent / "webapp_static"
MAX_AGE = 24 * 3600                     # initData старше суток не принимаем
REPO, CFG = web.AppKey("repo", Repo), web.AppKey("cfg", Config)


def verify_init_data(init_data: str, bot_token: str, now: float | None = None) -> dict | None:
    """Проверка подписи Telegram WebApp initData. Возвращает пользователя или None."""
    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=True))
    except ValueError:
        return None
    got = pairs.pop("hash", None)
    if not got:
        return None
    check = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    want = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(want, got):
        return None
    try:
        if (now or time.time()) - int(pairs.get("auth_date", "0")) > MAX_AGE:
            return None
        user = json.loads(pairs.get("user", "null"))
    except ValueError:
        return None
    return user if isinstance(user, dict) and isinstance(user.get("id"), int) else None


@web.middleware
async def security_headers(request: web.Request, handler):
    resp = await handler(request)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("Referrer-Policy", "no-referrer")
    resp.headers.setdefault("Content-Security-Policy",
                            "default-src 'self'; script-src 'self' https://telegram.org; style-src 'self'; "
                            "img-src 'self' data:; connect-src 'self'; frame-ancestors https://web.telegram.org "
                            "https://*.telegram.org")
    return resp


async def _auth(request: web.Request):
    """→ (tg_id, user row | None, lang). Ошибка 401, если подпись неверна."""
    head = request.headers.get("Authorization", "")
    user = verify_init_data(head[4:], request.app[CFG].bot_token) if head.startswith("tma ") else None
    if not user:
        raise web.HTTPUnauthorized(text='{"error":"auth"}', content_type="application/json")
    repo = request.app[REPO]
    tg_id = user["id"]
    u = await repo.get_user(tg_id)
    lang = (u["lang"] if u and u["lang"] else None) or detect(user.get("language_code"))
    return tg_id, u, lang


def _bad(msg: str, status: int = 400) -> web.Response:
    return web.json_response({"error": msg}, status=status)


def _rel_id(request: web.Request) -> int | None:
    raw = request.query.get("rel")
    if raw is None or raw == "":
        return None
    if not raw.isdigit():
        raise web.HTTPBadRequest(text='{"error":"rel"}', content_type="application/json")
    return int(raw)


async def _subject(request, tg_id: int, u):
    """Чья Луна: пользователя или близкого (?rel=id). → (имя | None, moon_rashi, moon_nakshatra)."""
    rid = _rel_id(request)
    if rid is None:
        return None, u["moon_rashi"], u["moon_nakshatra"]
    rel = await request.app[REPO].get_relative(tg_id, rid)
    if not rel:
        raise web.HTTPNotFound(text='{"error":"rel"}', content_type="application/json")
    name, prof = rel
    return name, prof.moon_rashi, prof.moon_nakshatra


# ------------------------------------------------------------------ API
async def api_me(request: web.Request) -> web.Response:
    tg_id, u, lang = await _auth(request)
    cfg = request.app[CFG]
    if not u or not u["has_birth"]:
        return web.json_response({"lang": lang, "has_birth": False})
    prof = await request.app[REPO].load_profile(tg_id)
    S, N, P = SIGN[lang], NAKSHATRA_NAME[lang], PLANET[lang]
    out = {"lang": lang, "has_birth": True, "premium": is_premium(u, cfg), "free_mode": cfg.free_mode,
           "place": city_name(u["city_key"], lang), "sun_west": S[prof.sun_trop_sign],
           "sun_sid": S[prof.sun_sid_rashi],
           "moon": S[prof.moon_rashi] if prof.moon_rashi is not None else None,
           "nakshatra": N[prof.moon_nakshatra] if prof.moon_nakshatra is not None else None,
           "lagna": S[prof.lagna_rashi] if prof.lagna_rashi is not None else None, "dasha": None}
    if prof.dashas:
        md, ad = prof.current_dasha(datetime.now(ZoneInfo(u["tz"])))
        if md:
            out["dasha"] = {"maha": P[md.lord], "antar": P[ad.lord] if ad else None,
                            "until": f"{ad.end[5:]}.{ad.end[:4]}" if ad else None}
    return web.json_response(out)


async def api_day(request: web.Request) -> web.Response:
    tg_id, u, lang = await _auth(request)
    if not u or not u["has_birth"]:
        return _bad("need_birth", 409)
    who, moon, nak = await _subject(request, tg_id, u)
    today = datetime.now(ZoneInfo(u["tz"])).date()
    try:
        d = date.fromisoformat(request.query["date"]) if request.query.get("date") else today
    except ValueError:
        return _bad("date")
    if abs((d - today).days) > 366:
        return _bad("date")
    full = is_premium(u, request.app[CFG])
    p = await asyncio.to_thread(daily_personal, d, settings_for(u["city_key"]), moon, nak)
    out = {"date": d.isoformat(), "label": f"{fmt_date(d, lang)}, {WEEKDAY_SHORT[lang][d.weekday()]}",
           "who": who, "place": city_name(u["city_key"], lang), "premium": full,
           "sky": describe_sky(p.info, lang), "special": special_text(p.info, lang)}
    if full:
        do, avoid = advice(p, lang)
        out.update(icon=p.icon, tone=p.tone, tone_text=p.tone_text(lang), reasons=reasons_text(p, lang),
                   do=do, avoid=avoid)
    return web.json_response(out)


async def api_period(request: web.Request) -> web.Response:
    from .period_view import build_period
    tg_id, u, lang = await _auth(request)
    if not u or not u["has_birth"]:
        return _bad("need_birth", 409)
    if not is_premium(u, request.app[CFG]):
        return _bad("premium", 402)
    try:
        days = int(request.query.get("days", "7"))
    except ValueError:
        return _bad("days")
    if days not in (7, 30):
        return _bad("days")
    who, moon, nak = await _subject(request, tg_id, u)
    start = datetime.now(ZoneInfo(u["tz"])).date()
    per = await asyncio.to_thread(build_period, start, start + timedelta(days=days - 1),
                                  settings_for(u["city_key"]), moon, nak)
    out_days = []
    for p in per.days:
        do, _ = advice(p, lang)
        out_days.append({"date": p.info.day.isoformat(),
                         "label": f"{fmt_date(p.info.day, lang, year=False)} {WEEKDAY_SHORT[lang][p.info.day.weekday()]}",
                         "icon": p.icon, "tone": p.tone, "tone_text": p.tone_text(lang), "score": p.score,
                         "nakshatra": NAKSHATRA_NAME[lang][p.info.nakshatra], "do": do[0],
                         "special": [s.split(" — ")[0] for s in special_text(p.info, lang)]})
    events = [{"when": f"{fmt_date(dt.date(), lang, year=False)} {dt:%H:%M}", "text": event_text(lang, e.as_dict())}
              for dt, e in per.events]
    return web.json_response({"who": who, "days": out_days, "events": events})


async def api_family(request: web.Request) -> web.Response:
    tg_id, u, lang = await _auth(request)
    items = await request.app[REPO].relatives(tg_id) if u else []
    return web.json_response({"items": [{"id": i, "name": n} for i, n in items]})


async def api_transits(request: web.Request) -> web.Response:
    from .transits_handlers import current
    from .transits_view import short_title
    _, _, lang = await _auth(request)
    tr = await asyncio.to_thread(current)
    return web.json_response({"items": [{"title": short_title(x, lang),
                                         "since": fmt_date(x.first_date, lang)} for x in tr]})


async def index(request: web.Request) -> web.FileResponse:
    return web.FileResponse(STATIC / "index.html", headers={"Cache-Control": "no-cache"})


def make_app(repo: Repo, cfg: Config) -> web.Application:
    app = web.Application(middlewares=[security_headers])
    app[REPO], app[CFG] = repo, cfg
    app.router.add_get("/", index)
    app.router.add_get("/api/me", api_me)
    app.router.add_get("/api/day", api_day)
    app.router.add_get("/api/period", api_period)
    app.router.add_get("/api/family", api_family)
    app.router.add_get("/api/transits", api_transits)
    app.router.add_static("/static/", STATIC, show_index=False)
    return app


async def start(repo: Repo, cfg: Config) -> web.AppRunner:
    runner = web.AppRunner(make_app(repo, cfg), access_log=None)      # без логов запросов: в них initData
    await runner.setup()
    await web.TCPSite(runner, "127.0.0.1", cfg.webapp_port).start()
    return runner
