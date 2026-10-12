"""Работа с PostgreSQL (asyncpg). Данные рождения не храним — только астропрофиль."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import asyncpg

from jyotish.profile import PLANET_ORDER, AstroProfile

log = logging.getLogger("db")


class Repo:
    def __init__(self, pool: asyncpg.Pool, fernet_key: str | None = None):
        self.pool = pool
        self.fernet_key = fernet_key          # нужен только для разовой миграции старых записей

    @classmethod
    async def create(cls, dsn: str, fernet_key: str | None = None) -> "Repo":
        pool = await asyncpg.create_pool(dsn, min_size=1, max_size=5)
        return cls(pool, fernet_key)

    # --------------------------------------------------------- users
    async def ensure_user(self, tg_id: int) -> asyncpg.Record:
        return await self.pool.fetchrow(
            """INSERT INTO users (tg_id) VALUES ($1)
               ON CONFLICT (tg_id) DO UPDATE SET tg_id = EXCLUDED.tg_id
               RETURNING *""", tg_id)

    async def get_user(self, tg_id: int) -> asyncpg.Record | None:
        return await self.pool.fetchrow(
            """SELECT u.*, b.moon_rashi, b.sun_sid_rashi, b.sun_trop_sign, b.lagna_rashi,
                      b.moon_nakshatra, b.moon_pada, b.moon_first_half, b.time_known,
                      b.user_id IS NOT NULL AS has_birth
               FROM users u LEFT JOIN profiles b ON b.user_id = u.id
               WHERE u.tg_id = $1""", tg_id)

    async def set_lang(self, tg_id: int, lang: str) -> None:
        await self.pool.execute("UPDATE users SET lang = $2 WHERE tg_id = $1", tg_id, lang)

    async def get_lang(self, tg_id: int) -> str | None:
        return await self.pool.fetchval("SELECT lang FROM users WHERE tg_id = $1", tg_id)

    async def set_consent(self, tg_id: int) -> None:
        await self.pool.execute("UPDATE users SET consent_pd_at = now() WHERE tg_id = $1", tg_id)

    async def set_mode(self, tg_id: int, mode: str) -> None:
        await self.pool.execute("UPDATE users SET sign_mode = $2 WHERE tg_id = $1", tg_id, mode)

    async def set_city(self, tg_id: int, city_key: str, tz: str) -> None:
        await self.pool.execute("UPDATE users SET city_key = $2, tz = $3 WHERE tg_id = $1",
                                tg_id, city_key, tz)

    async def delete_user(self, tg_id: int) -> None:
        await self.pool.execute("DELETE FROM users WHERE tg_id = $1", tg_id)

    # --------------------------------------------------------- профиль
    @staticmethod
    def _profile_args(p: AstroProfile) -> list:
        return [p.time_known, p.moon_rashi, p.sun_sid_rashi, p.sun_trop_sign, p.lagna_rashi,
                p.moon_nakshatra, p.moon_pada, p.moon_first_half,
                [p.planet_rashi[c] for c in PLANET_ORDER], json.dumps(p.dashas_json())]

    async def save_profile(self, tg_id: int, p: AstroProfile) -> None:
        uid = (await self.ensure_user(tg_id))["id"]
        await self.pool.execute(
            """INSERT INTO profiles (user_id, time_known, moon_rashi, sun_sid_rashi, sun_trop_sign,
                       lagna_rashi, moon_nakshatra, moon_pada, moon_first_half, planet_rashi, dashas)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
               ON CONFLICT (user_id) DO UPDATE SET time_known = EXCLUDED.time_known,
                   moon_rashi = EXCLUDED.moon_rashi, sun_sid_rashi = EXCLUDED.sun_sid_rashi,
                   sun_trop_sign = EXCLUDED.sun_trop_sign, lagna_rashi = EXCLUDED.lagna_rashi,
                   moon_nakshatra = EXCLUDED.moon_nakshatra, moon_pada = EXCLUDED.moon_pada,
                   moon_first_half = EXCLUDED.moon_first_half, planet_rashi = EXCLUDED.planet_rashi,
                   dashas = EXCLUDED.dashas, updated_at = now()""",
            uid, *self._profile_args(p))

    async def load_profile(self, tg_id: int) -> AstroProfile | None:
        r = await self.pool.fetchrow(
            """SELECT b.* FROM profiles b JOIN users u ON u.id = b.user_id WHERE u.tg_id = $1""", tg_id)
        return self._row_profile(r) if r else None

    @staticmethod
    def _row_profile(r) -> AstroProfile:
        pr = r["planet_rashi"] or []
        moon = r["moon_rashi"]
        return AstroProfile(
            time_known=r["time_known"], sun_trop_sign=r["sun_trop_sign"], sun_sid_rashi=r["sun_sid_rashi"],
            moon_rashi=moon, moon_candidates=[moon] if moon is not None else [],
            moon_nakshatra=r["moon_nakshatra"], moon_pada=r["moon_pada"], moon_first_half=r["moon_first_half"],
            lagna_rashi=r["lagna_rashi"], planet_rashi=dict(zip(PLANET_ORDER, pr)),
            dashas=AstroProfile.dashas_from_json(json.loads(r["dashas"]) if r["dashas"] else []))

    # --------------------------------------------------------- близкие
    async def add_relative(self, tg_id: int, name: str, p: AstroProfile, limit: int = 10) -> int | None:
        """Сохраняет профиль близкого. None — достигнут лимит."""
        uid = (await self.ensure_user(tg_id))["id"]
        async with self.pool.acquire() as con, con.transaction():
            await con.execute("SELECT 1 FROM users WHERE id = $1 FOR UPDATE", uid)
            if await con.fetchval("SELECT count(*) FROM relatives WHERE user_id = $1", uid) >= limit:
                return None
            return await con.fetchval(
                """INSERT INTO relatives (user_id, name, time_known, moon_rashi, sun_sid_rashi, sun_trop_sign,
                       lagna_rashi, moon_nakshatra, moon_pada, moon_first_half, planet_rashi, dashas)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12) RETURNING id""",
                uid, name, *self._profile_args(p))

    async def relatives(self, tg_id: int) -> list[tuple[int, str]]:
        rows = await self.pool.fetch(
            """SELECT r.id, r.name FROM relatives r JOIN users u ON u.id = r.user_id
               WHERE u.tg_id = $1 ORDER BY r.id""", tg_id)
        return [(r["id"], r["name"]) for r in rows]

    async def get_relative(self, tg_id: int, rel_id: int) -> tuple[str, AstroProfile] | None:
        r = await self.pool.fetchrow(
            """SELECT r.* FROM relatives r JOIN users u ON u.id = r.user_id
               WHERE u.tg_id = $1 AND r.id = $2""", tg_id, rel_id)
        return (r["name"], self._row_profile(r)) if r else None

    async def delete_relative(self, tg_id: int, rel_id: int) -> bool:
        res = await self.pool.execute(
            """DELETE FROM relatives r USING users u WHERE u.id = r.user_id AND u.tg_id = $1 AND r.id = $2""",
            tg_id, rel_id)
        return res.endswith(" 1")

    # --------------------------------------------------------- forecasts
    async def save_run(self, kind: str, event_at: datetime, period_end: datetime, city_key: str,
                       ayanamsha: str, true_node: bool, facts: dict) -> tuple[int, bool]:
        """Возвращает (id, новая ли запись). Повторный вызов для той же лунации не дублирует."""
        row = await self.pool.fetchrow(
            """INSERT INTO forecast_runs (kind, event_at, period_end, city_key, ayanamsha, true_node, facts)
               VALUES ($1,$2,$3,$4,$5,$6,$7)
               ON CONFLICT (kind, event_at, city_key, ayanamsha, true_node) DO NOTHING
               RETURNING id""",
            kind, event_at, period_end, city_key, ayanamsha, true_node, json.dumps(facts, ensure_ascii=False))
        if row:
            return row["id"], True
        rid = await self.pool.fetchval(
            """SELECT id FROM forecast_runs WHERE kind=$1 AND event_at=$2 AND city_key=$3
               AND ayanamsha=$4 AND true_node=$5""", kind, event_at, city_key, ayanamsha, true_node)
        return rid, False

    async def save_text(self, run_id: int, mode: str, sign: int, channel: str, body: str,
                        status: str = "published") -> None:
        await self.pool.execute(
            """INSERT INTO forecast_texts (run_id, sign_mode, sign, channel, body, status, published_at)
               VALUES ($1,$2,$3,$4,$5,$6, CASE WHEN $6='published' THEN now() END)
               ON CONFLICT (run_id, sign_mode, sign, channel, style) DO UPDATE SET body = EXCLUDED.body""",
            run_id, mode, sign, channel, body, status)

    async def subscribers(self, city_key: str) -> list[asyncpg.Record]:
        return await self.pool.fetch(
            """SELECT u.tg_id, u.sign_mode, u.lang, b.moon_rashi, b.sun_sid_rashi, b.sun_trop_sign
               FROM users u JOIN profiles b ON b.user_id = u.id
               WHERE u.city_key = $1 AND u.consent_pd_at IS NOT NULL AND u.tg_id IS NOT NULL""",
            city_key)

    async def cities_in_use(self) -> list[str]:
        return [r["city_key"] for r in await self.pool.fetch("SELECT DISTINCT city_key FROM users")]

    # --------------------------------------------------------- премиум
    @staticmethod
    def premium_active(u: asyncpg.Record | dict | None) -> bool:
        if not u or not u["premium_until"]:
            return False
        return u["premium_until"] > datetime.now(timezone.utc)

    async def start_trial(self, tg_id: int, days: int) -> datetime | None:
        """Пробный период — один раз на пользователя. Возвращает новую дату окончания или None."""
        return await self.pool.fetchval(
            """UPDATE users SET trial_used = true,
                   premium_until = GREATEST(COALESCE(premium_until, now()), now()) + make_interval(days => $2)
               WHERE tg_id = $1 AND NOT trial_used RETURNING premium_until""", tg_id, days)

    async def extend_premium(self, tg_id: int, days: int) -> datetime | None:
        return await self.pool.fetchval(
            """UPDATE users SET premium_until =
                   GREATEST(COALESCE(premium_until, now()), now()) + make_interval(days => $2)
               WHERE tg_id = $1 RETURNING premium_until""", tg_id, days)

    async def set_subscription(self, tg_id: int, charge_id: str, until: datetime) -> None:
        await self.pool.execute(
            """UPDATE users SET sub_charge_id = $2, sub_canceled = false,
                   premium_until = GREATEST(COALESCE(premium_until, now()), $3)
               WHERE tg_id = $1""", tg_id, charge_id, until)

    async def set_sub_canceled(self, tg_id: int, canceled: bool) -> None:
        await self.pool.execute("UPDATE users SET sub_canceled = $2 WHERE tg_id = $1", tg_id, canceled)

    async def record_payment(self, tg_id: int, charge_id: str, product: str, stars: int,
                             recurring: bool) -> bool:
        """True — платёж новый; False — уже записан (повторная доставка апдейта)."""
        row = await self.pool.fetchval(
            """INSERT INTO payments (tg_id, charge_id, product, stars, is_recurring)
               VALUES ($1,$2,$3,$4,$5) ON CONFLICT (charge_id) DO NOTHING RETURNING id""",
            tg_id, charge_id, product, stars, recurring)
        return row is not None

    async def mark_refunded(self, charge_id: str) -> asyncpg.Record | None:
        return await self.pool.fetchrow(
            """UPDATE payments SET refunded_at = now()
               WHERE charge_id = $1 AND refunded_at IS NULL RETURNING *""", charge_id)

    async def add_compat_credit(self, tg_id: int, n: int = 1) -> None:
        await self.pool.execute("UPDATE users SET compat_credits = compat_credits + $2 WHERE tg_id = $1",
                                tg_id, n)

    async def add_report_credit(self, tg_id: int, n: int = 1) -> None:
        await self.pool.execute("UPDATE users SET report_credits = report_credits + $2 WHERE tg_id = $1", tg_id, n)

    async def use_report_credit(self, tg_id: int) -> bool:
        return await self.pool.fetchval(
            """UPDATE users SET report_credits = report_credits - 1
               WHERE tg_id = $1 AND report_credits > 0 RETURNING true""", tg_id) is not None

    async def use_compat_credit(self, tg_id: int) -> bool:
        return await self.pool.fetchval(
            """UPDATE users SET compat_credits = compat_credits - 1
               WHERE tg_id = $1 AND compat_credits > 0 RETURNING true""", tg_id) is not None

    # --------------------------------------------------------- рефералы
    async def set_referrer(self, tg_id: int, ref_tg_id: int) -> bool:
        """Запоминаем пригласившего только для новичка без данных рождения."""
        if tg_id == ref_tg_id:
            return False
        return await self.pool.fetchval(
            """UPDATE users u SET referred_by = $2
               WHERE u.tg_id = $1 AND u.referred_by IS NULL
                 AND NOT EXISTS (SELECT 1 FROM profiles b WHERE b.user_id = u.id)
                 AND EXISTS (SELECT 1 FROM users r WHERE r.tg_id = $2)
               RETURNING true""", tg_id, ref_tg_id) is not None

    async def claim_referral(self, tg_id: int) -> int | None:
        """Один раз: возвращает tg_id пригласившего, которому положен бонус."""
        return await self.pool.fetchval(
            """UPDATE users SET ref_rewarded = true
               WHERE tg_id = $1 AND referred_by IS NOT NULL AND NOT ref_rewarded
               RETURNING referred_by""", tg_id)

    async def referrals_count(self, tg_id: int) -> int:
        return await self.pool.fetchval(
            "SELECT count(*) FROM users WHERE referred_by = $1 AND ref_rewarded", tg_id)

    # --------------------------------------------------------- утренняя рассылка
    async def set_daily_push(self, tg_id: int, on: bool) -> None:
        await self.pool.execute("UPDATE users SET daily_push = $2 WHERE tg_id = $1", tg_id, on)

    async def daily_candidates(self, promo: bool = False) -> list[asyncpg.Record]:
        return await self.pool.fetch(
            """SELECT u.id, u.tg_id, u.tz, u.city_key, u.sign_mode, u.lang, b.moon_rashi, b.moon_nakshatra,
                      b.sun_sid_rashi, b.sun_trop_sign
               FROM users u JOIN profiles b ON b.user_id = u.id
               WHERE u.daily_push AND (u.premium_until > now() OR $1) AND u.consent_pd_at IS NOT NULL""",
            promo)

    async def mark_daily_sent(self, user_id: int, day) -> bool:
        return await self.pool.fetchval(
            """INSERT INTO daily_sent (user_id, day) VALUES ($1, $2)
               ON CONFLICT DO NOTHING RETURNING true""", user_id, day) is not None

    # --------------------------------------------------------- пуши о транзитах
    async def transit_push_candidates(self) -> list[asyncpg.Record]:
        return await self.pool.fetch(
            """SELECT u.id, u.tg_id, u.tz, u.city_key, u.sign_mode, u.lang, b.moon_rashi, b.sun_sid_rashi, b.sun_trop_sign
               FROM users u JOIN profiles b ON b.user_id = u.id
               WHERE u.consent_pd_at IS NOT NULL AND u.tg_id IS NOT NULL""")

    async def mark_transit_push(self, user_id: int, key: str, stage: str) -> bool:
        return await self.pool.fetchval(
            """INSERT INTO transit_pushes (user_id, key, stage) VALUES ($1, $2, $3)
               ON CONFLICT DO NOTHING RETURNING true""", user_id, key, stage) is not None

    # --------------------------------------------------------- миграции
    async def migrate(self, folder: str) -> list[str]:
        """Применяет migrations/NNN_*.sql, которых ещё нет в schema_migrations.

        Перед файлом может выполниться Python-хук (см. HOOKS) в той же транзакции."""
        import pathlib
        await self.pool.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY, applied_at TIMESTAMPTZ DEFAULT now())")
        done = {r["name"] for r in await self.pool.fetch("SELECT name FROM schema_migrations")}
        applied = []
        for f in sorted(pathlib.Path(folder).glob("*.sql")):
            if f.name in done:
                continue
            async with self.pool.acquire() as con, con.transaction():
                hook = HOOKS.get(f.name)
                if hook:
                    await hook(self, con)
                await con.execute(f.read_text(encoding="utf-8"))
                await con.execute("INSERT INTO schema_migrations (name) VALUES ($1)", f.name)
            applied.append(f.name)
        return applied


# ------------------------------------------------------------------ хуки миграций
async def _profiles_from_encrypted(repo: Repo, con) -> None:
    """Перед удалением birth_enc: пересчитать профиль из старых зашифрованных данных рождения."""
    from cryptography.fernet import Fernet

    from jyotish.profile import compute

    rows = await con.fetch(
        """SELECT b.user_id, u.tg_id, b.birth_enc FROM birth_data b JOIN users u ON u.id = b.user_id
           WHERE b.birth_enc IS NOT NULL""")
    if not rows:
        return
    if not repo.fernet_key:
        raise RuntimeError("FERNET_KEY нужен для разовой миграции данных рождения в профили")
    f = Fernet(repo.fernet_key.encode())
    for r in rows:
        b = json.loads(f.decrypt(bytes(r["birth_enc"])))
        birth = datetime.strptime(f"{b['date']} {b['time']}", "%Y-%m-%d %H:%M")
        p = compute(birth, b["lat"], b["lon"], b["tz"], b["time_known"])
        await con.execute(
            """UPDATE birth_data SET time_known=$2, moon_rashi=$3, sun_sid_rashi=$4, sun_trop_sign=$5,
                   lagna_rashi=$6, moon_nakshatra=$7, moon_pada=$8, moon_first_half=$9, planet_rashi=$10,
                   dashas=$11, updated_at=now() WHERE user_id=$1""",
            r["user_id"], *Repo._profile_args(p))
    log.info("профили пересчитаны из данных рождения: %d", len(rows))


HOOKS = {"003_drop_birth_data.sql": _profiles_from_encrypted}
