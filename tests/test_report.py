"""PDF-разбор натальной карты: анализ, тексты, PDF и сценарий покупки."""
import io
import re
import time
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest
from aiogram.methods import SendDocument, SendInvoice

from bot.report_pdf import build_pdf, sections, summary
from jyotish.core import Location
from jyotish.natal import build_chart
from jyotish.report import analyze, dignity
from tests.conftest import cb, msg
from tests.test_bot_flow import U, _payment_update, register

CYR = re.compile(r"[А-Яа-яЁё]")
MSK = ZoneInfo("Europe/Moscow")
LOC = Location("СПб", 59.93, 30.33, "Europe/Moscow")
CH = build_chart(datetime(1980, 5, 14, 6, 30, tzinfo=MSK), LOC)
NOW = datetime(2026, 10, 11, tzinfo=ZoneInfo("UTC"))
R = analyze(CH, NOW)


def test_dignity_rules():
    assert dignity("Su", 0) == "exalted" and dignity("Su", 6) == "debilitated"
    assert dignity("Sa", 9) == "own" and dignity("Mo", 7) == "debilitated"
    assert dignity("Ju", 4) == "friend" and dignity("Ve", 4) == "enemy"
    assert dignity("Ra", 3) is None


def test_analysis_of_sample_chart():
    codes = {y.code for y in R.yogas}
    assert {"raja", "dhana"} <= codes
    assert R.planet("Su").dignity == "exalted" and R.planet("Sa").retro
    assert len(R.house_lords) == 12 and R.dashas[0].current and R.antardasha.lord == "Sa"


def test_budha_aditya_detected_when_sun_and_mercury_share_a_sign():
    ch = build_chart(datetime(1990, 1, 10, 12, 0, tzinfo=MSK), LOC)
    r = analyze(ch, NOW)
    same = ch.planets["Su"].rashi == ch.planets["Me"].rashi
    assert same == any(y.code == "budha_aditya" for y in r.yogas)


@pytest.mark.parametrize("lang", ["ru", "en"])
def test_sections_cover_everything(lang):
    secs = sections(R, lang)
    text = "\n".join(t for _, items in secs for _, t in items)
    assert len(secs) >= 7
    planet_heads = [t for _, items in secs for st, t in items if st == "h2" and "°" in t]
    assert len(planet_heads) == 9
    if lang == "en":
        assert not CYR.search(text + "".join(title for title, _ in secs))


@pytest.mark.parametrize("lang", ["ru", "en"])
@pytest.mark.parametrize("known", [True, False])
def test_pdf_builds(lang, known):
    ch = CH if known else build_chart(datetime(1980, 5, 14, 12, 0, tzinfo=MSK), LOC)
    pdf = build_pdf(ch, analyze(ch, NOW, known), lang, "X")
    assert pdf[:5] == b"%PDF-" and len(pdf) > 20_000


def test_summary_mentions_lagna_moon_dasha():
    s = summary(R, "ru")
    assert "Близнецы" in s and "Бхарани" in s and "Юпитер" in s


async def _chart(dp, bot):
    await dp.feed_update(bot, msg(U, "/chart"))
    await dp.feed_update(bot, msg(U, "14.05.1980"))
    await dp.feed_update(bot, msg(U, "06:30"))
    await dp.feed_update(bot, cb(U, "cplace:spb"))


@pytest.mark.asyncio
async def test_report_free_during_promo(tg, repo):
    dp, bot, fake, cfg = tg
    await register(dp, bot)
    cfg.free_until = date(2099, 1, 1)
    await _chart(dp, bot)
    fake.calls.clear()
    await dp.feed_update(bot, cb(U, "rep:get"))
    docs = fake.of(SendDocument)
    assert docs and docs[0].document.filename == "razbor_karty.pdf"
    fake.calls.clear()
    await dp.feed_update(bot, cb(U, "rep:get"))                    # данные стёрты после выдачи
    assert "стёрты" in fake.texts(U)[-1]


@pytest.mark.asyncio
async def test_report_paid_flow(tg, repo):
    dp, bot, fake, cfg = tg
    await register(dp, bot)
    await _chart(dp, bot)
    fake.calls.clear()
    await dp.feed_update(bot, cb(U, "rep:get"))
    inv = fake.of(SendInvoice)
    assert inv and inv[0].payload == "report" and inv[0].prices[0].amount == cfg.price_report
    await dp.feed_update(bot, _payment_update(U, "report", cfg.price_report, "rp_1"))
    assert fake.of(SendDocument)                                   # карта ещё в памяти — PDF сразу
    assert (await repo.get_user(U))["report_credits"] == 0


@pytest.mark.asyncio
async def test_report_payment_without_chart_keeps_credit(tg, repo):
    dp, bot, fake, cfg = tg
    await register(dp, bot)
    await dp.feed_update(bot, _payment_update(U, "report", cfg.price_report, "rp_2"))
    assert "Постройте карту" in fake.texts(U)[-1]
    assert (await repo.get_user(U))["report_credits"] == 1
    fake.calls.clear()
    await _chart(dp, bot)
    await dp.feed_update(bot, cb(U, "rep:get"))                    # кредит тратится на следующий отчёт
    assert fake.of(SendDocument) and (await repo.get_user(U))["report_credits"] == 0


@pytest.mark.asyncio
async def test_chart_data_expires(tg, repo, monkeypatch):
    from bot import report_flow
    dp, bot, fake, cfg = tg
    await register(dp, bot)
    cfg.free_until = date(2099, 1, 1)
    await _chart(dp, bot)
    real = time.time
    monkeypatch.setattr(report_flow.time, "time", lambda: real() + report_flow.TTL + 5)
    fake.calls.clear()
    await dp.feed_update(bot, cb(U, "rep:get"))
    assert not fake.of(SendDocument) and "30" in fake.texts(U)[-1]


def test_pdf_has_cyrillic_font():
    import pymupdf
    doc = pymupdf.open(stream=io.BytesIO(build_pdf(CH, R, "ru", "СПб")).getvalue(), filetype="pdf")
    text = "".join(p.get_text() for p in doc)
    assert "Лагна" in text and "Планеты в вашей карте" in text


@pytest.mark.asyncio
async def test_chart_data_wiped_by_timer_without_user_action(tg, repo, monkeypatch):
    """Данные стираются сами по истечении TTL, а не только при следующем обращении."""
    import asyncio
    from bot import report_flow
    dp, bot, fake, cfg = tg
    await register(dp, bot)
    monkeypatch.setattr(report_flow, "TTL", 0.05)
    await _chart(dp, bot)
    task = next(iter(report_flow._timers.values()))
    await asyncio.wait_for(task, 2)
    from aiogram.fsm.storage.base import StorageKey
    key = StorageKey(bot_id=bot.id, chat_id=U, user_id=U)
    assert await dp.storage.get_data(key) == {}


@pytest.mark.asyncio
async def test_abandoned_input_is_swept(tg, repo):
    """Брошенный на середине ввод (дата рождения) стирается из памяти по TTL."""
    dp, bot, fake, cfg = tg
    await register(dp, bot)
    await dp.feed_update(bot, msg(U, "/compat"))
    await dp.feed_update(bot, cb(U, "cg:f"))
    await dp.feed_update(bot, msg(U, "02.03.1985"))                # дата партнёра в памяти
    st = dp.storage
    assert any("p_date" in rec.data for rec in st.storage.values())
    assert st.sweep(now=time.time() + st.ttl + 1) >= 1
    assert not any(rec.data for rec in st.storage.values())
