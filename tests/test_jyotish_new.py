from datetime import date

import pytest

from jyotish.compat import NAK_SPAN, VASHYA_TABLE, YONI_TABLE, compat
from jyotish.core import CITIES, Settings
from jyotish.daily import TARA_SCORE, chandra_house, day_info, personal_day, tara_index
from jyotish.texts import TARA
from jyotish.muhurta import CATEGORIES, build_calendar, day_blocked

MSK = Settings(location=CITIES["moscow"])


def lon(nak: int, frac: float = 0.5) -> float:
    return (nak + frac) * NAK_SPAN


# ------------------------------------------------------------------ daily
def test_day_info_matches_drik_panchang_moscow_2026_10_11():
    # Drik Panchang, Москва: восход 06:52, Читра до 20:02, Пратипада, воскресенье
    i = day_info(date(2026, 10, 11), MSK)
    assert abs((i.sunrise.hour * 60 + i.sunrise.minute) - (6 * 60 + 52)) <= 2
    assert i.nakshatra == 13 and i.tithi == 1 and i.vara == 6
    assert i.nak_change and (i.nak_change.hour, i.nak_change.minute) == (20, 2)


def test_amavasya_detected():
    i = day_info(date(2026, 11, 9), MSK)
    assert i.tithi == 30 and day_blocked(i)


def test_tara_and_chandra():
    assert tara_index(0, 0) == 0
    assert TARA["ru"][tara_index(0, 1)][0] == "Сампат" and TARA["en"][1][0] == "Sampat"
    assert tara_index(0, 9) == 0 and tara_index(0, 14) == 5
    assert chandra_house(0, 0) == 1 and chandra_house(11, 0) == 2


def test_personal_day_without_birth_data_is_neutral():
    p = personal_day(day_info(date(2026, 10, 11), MSK), None, None)
    assert p.tara is None and p.chandra is None and p.tone == "calm"


# ------------------------------------------------------------------ muhurta
def test_calendar_excludes_blocked_days_and_respects_personal():
    cal = build_calendar(date(2026, 10, 11), 30, 6, 15, MSK)
    assert len(cal.days) == 30
    for cat in CATEGORIES:
        for p in cal.best[cat.key]:
            assert not day_blocked(p.info)
            assert p.info.vara in cat.varas and p.info.nakshatra in cat.naks
            assert TARA_SCORE[p.tara] >= 0
    assert any(p.info.tithi == 30 for p in cal.avoid)


# ------------------------------------------------------------------ compat
def test_tables_are_symmetric_where_classical():
    for i in range(14):
        for j in range(14):
            assert YONI_TABLE[i][j] == YONI_TABLE[j][i]
    assert all(len(r) == 5 for r in VASHYA_TABLE)


def test_same_nakshatra_gives_28_with_nadi_dosha():
    r = compat(lon(3, 0.1), lon(3, 0.9))     # Рохини, разные пады
    assert r.total == 28
    assert any(d["code"] == "nadi" and d["cancelled"] for d in r.doshas)


@pytest.mark.parametrize("a", range(0, 27, 4))
@pytest.mark.parametrize("b", range(1, 27, 5))
def test_scores_in_bounds(a, b):
    r = compat(lon(a), lon(b))
    assert 0 <= r.total <= 36
    assert all(0 <= k.score <= k.max for k in r.kutas)
    assert sum(k.max for k in r.kutas) == 36


def test_bhakoot_dosha_6_8():
    r = compat(lon(0), 7 * 30 + 5)          # Овен и Скорпион — 6/8
    assert next(k for k in r.kutas if k.code == "bhakoot").score == 0
