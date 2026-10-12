from datetime import datetime
from zoneinfo import ZoneInfo

from jyotish.compat import compat
from jyotish.core import Location, Settings, body, to_jd
from jyotish.natal import build_chart, current_dasha
from jyotish.profile import AstroProfile, MoonPoint, compute

TZ = "Europe/Moscow"
BIRTH = datetime(1980, 5, 14, 6, 30)


def test_profile_matches_full_chart():
    p = compute(BIRTH, 59.93, 30.33, TZ, True)
    ch = build_chart(BIRTH.replace(tzinfo=ZoneInfo(TZ)), Location("x", 59.93, 30.33, TZ))
    assert p.lagna_rashi == ch.lagna_rashi and p.moon_rashi == ch.moon_rashi
    assert p.moon_nakshatra == ch.planets["Mo"].nakshatra and p.moon_pada == ch.planets["Mo"].pada
    assert p.planet_rashi == {c: b.rashi for c, b in ch.planets.items()}
    now = datetime(2026, 10, 11, tzinfo=ZoneInfo(TZ))
    md, ad = current_dasha(ch.dashas, to_jd(now))
    pmd, pad = p.current_dasha(now)
    assert (pmd.lord, pad.lord) == (md.lord, ad.lord)


def test_profile_has_no_birth_datetime():
    p = compute(BIRTH, 59.93, 30.33, TZ, True)
    blob = repr(p) + repr(p.dashas_json())
    assert "1980-05-14" not in blob and "06:30" not in blob
    assert all(len(d["start"]) == 7 for d in p.dashas_json())      # только год-месяц


def test_dashas_roundtrip_json():
    p = compute(BIRTH, 59.93, 30.33, TZ, True)
    assert AstroProfile.dashas_from_json(p.dashas_json()) == p.dashas


def test_without_time_no_lagna_no_dashas():
    p = compute(datetime(1985, 3, 2), 55.75, 37.62, TZ, False)
    assert p.lagna_rashi is None and p.dashas == [] and not p.time_known


def test_compat_from_profile_equals_compat_from_longitude():
    a = compute(BIRTH, 59.93, 30.33, TZ, True)
    b_dt = datetime(1984, 9, 3, 21, 15, tzinfo=ZoneInfo(TZ))
    b_lon = body(to_jd(b_dt), "Mo", Settings()).lon
    a_lon = body(to_jd(BIRTH.replace(tzinfo=ZoneInfo(TZ))), "Mo", Settings()).lon
    assert compat(a.moon, MoonPoint.from_lon(b_lon)).total == compat(a_lon, b_lon).total
