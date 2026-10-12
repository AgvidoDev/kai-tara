"""Миграция 003: старые зашифрованные данные рождения → профиль, исходные данные стираются."""
import json
from datetime import datetime

import asyncpg
import pytest
from cryptography.fernet import Fernet

from bot.db import Repo
from jyotish.profile import compute
from tests.conftest import ROOT

pytestmark = pytest.mark.asyncio


async def test_encrypted_birth_data_migrates_to_profile(pg_uri):
    key = Fernet.generate_key().decode()
    con = await asyncpg.connect(pg_uri)
    await con.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    await con.execute((ROOT / "schema.sql").read_text(encoding="utf-8"))
    await con.execute("CREATE TABLE schema_migrations (name TEXT PRIMARY KEY, applied_at TIMESTAMPTZ DEFAULT now())")
    for name in ("001_monetization.sql", "002_profile_columns.sql"):
        await con.execute((ROOT / "migrations" / name).read_text(encoding="utf-8"))
        await con.execute("INSERT INTO schema_migrations (name) VALUES ($1)", name)
    uid = await con.fetchval("INSERT INTO users (tg_id) VALUES (777) RETURNING id")
    birth = {"date": "1980-05-14", "time": "06:30", "time_known": True, "lat": 59.93, "lon": 30.33,
             "tz": "Europe/Moscow", "place": "СПб"}
    blob = Fernet(key.encode()).encrypt(json.dumps(birth).encode())
    await con.execute("INSERT INTO birth_data (user_id, birth_enc, time_known, sun_trop_sign, sun_sid_rashi) "
                      "VALUES ($1, $2, true, 0, 0)", uid, blob)
    await con.close()

    repo = await Repo.create(pg_uri, key)
    assert "003_drop_birth_data.sql" in await repo.migrate(str(ROOT / "migrations"))
    cols = {r["column_name"] for r in await repo.pool.fetch(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'profiles'")}
    assert "birth_enc" not in cols
    assert await repo.pool.fetchval("SELECT to_regclass('public.birth_data')") is None
    p = await repo.load_profile(777)
    expected = compute(datetime(1980, 5, 14, 6, 30), 59.93, 30.33, "Europe/Moscow", True)
    assert p == expected
    await repo.pool.close()


async def test_migration_refuses_without_key(pg_uri):
    con = await asyncpg.connect(pg_uri)
    await con.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    await con.execute((ROOT / "schema.sql").read_text(encoding="utf-8"))
    uid = await con.fetchval("INSERT INTO users (tg_id) VALUES (778) RETURNING id")
    await con.execute("INSERT INTO birth_data (user_id, birth_enc, sun_trop_sign, sun_sid_rashi) "
                      "VALUES ($1, 'x', 0, 0)", uid)
    await con.close()
    repo = await Repo.create(pg_uri, None)
    with pytest.raises(RuntimeError, match="FERNET_KEY"):
        await repo.migrate(str(ROOT / "migrations"))
    # данные не потеряны: транзакция 003 откатилась
    assert await repo.pool.fetchval("SELECT count(*) FROM birth_data WHERE birth_enc IS NOT NULL") == 1
    await repo.pool.close()
