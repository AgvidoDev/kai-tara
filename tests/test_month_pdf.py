"""Персональный прогноз на 30 дней (PDF)."""
from datetime import date, datetime

import pymupdf
import pytest
from aiogram.methods import SendDocument

from bot.astro_service import settings_for
from bot.month_pdf import build_month_pdf
from jyotish.profile import compute
from tests.conftest import cb, msg
from tests.test_bot_flow import U, register

PROF = compute(datetime(1980, 5, 14, 6, 30), 59.93, 30.33, "Europe/Moscow", True)


@pytest.mark.parametrize("lang", ["ru", "en"])
def test_month_pdf_content(lang):
    pdf = build_month_pdf(date(2026, 10, 12), settings_for("moscow"), PROF, "X", ["Jupiter → Leo"], lang)
    doc = pymupdf.open(stream=pdf, filetype="pdf")
    text = "".join(p.get_text() for p in doc)
    if lang == "ru":
        assert "Персональный прогноз на 30 дней" in text and "Махадаша" in text and "По дням" in text
        assert "10.11" in text                                       # 30-й день
    else:
        assert "Personal forecast for 30 days" in text and "Day by day" in text
    fonts = {f[3] for p in doc for f in p.get_fonts()}
    assert any("Bold" in f or "bold" in f for f in fonts)           # жирное начертание подключено


@pytest.mark.asyncio
async def test_pdf30_from_month(tg, repo):
    dp, bot, fake, _ = tg
    await register(dp, bot)
    fake.calls.clear()
    await dp.feed_update(bot, cb(U, "pdf30"))
    docs = fake.of(SendDocument)
    assert docs and docs[0].document.filename == "kai_tara_30_days.pdf"
