"""Ввод места: город по названию (поиск GeoNames), кнопка популярного города, координаты или геолокация."""
from __future__ import annotations

import re

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from timezonefinder import TimezoneFinder

from jyotish import geo
from jyotish.core import CITIES, city_name

from .i18n import t

_tf = TimezoneFinder()
COORDS = re.compile(r"\s*(-?\d+(?:\.\d+)?)\s*[,; ]\s*(-?\d+(?:\.\d+)?)\s*")
DOMINANT = 20          # во сколько раз город должен быть крупнее следующего, чтобы выбрать без вопроса

Place = tuple[float, float, str, str, str | None]   # lat, lon, tz, название для показа, ключ города


def tz_at(lat: float, lon: float) -> str:
    return _tf.timezone_at(lat=lat, lng=lon) or "UTC"


def from_key(key: str, lang: str = "ru") -> Place | None:
    """Популярный город из CITIES или найденный (gn<id>)."""
    if key in CITIES:
        loc = CITIES[key]
        return loc.lat, loc.lon, loc.tz, city_name(key, lang), key
    c = geo.by_key(key)
    return (c.lat, c.lon, c.tz, c.label(lang), c.key) if c else None


def _auto(query: str, found: list[geo.City]) -> geo.City | None:
    q = geo.norm(query.split(",")[0])
    if len(found) == 1:
        return found[0]
    top, second = found[0], found[1]
    named = q in (geo.norm(top.ru), geo.norm(top.en))
    return top if named and top.pop >= DOMINANT * max(second.pop, 1) else None


async def resolve_text(m: Message, lang: str, prefix: str) -> Place | None:
    """Разбирает ввод: координаты → место; название → город или кнопки выбора. None — ждём выбора/повтора."""
    text = (m.text or "").strip()
    mt = COORDS.fullmatch(text)
    if mt:
        lat, lon = float(mt[1]), float(mt[2])
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            await m.answer(t(lang, "coords_range"))
            return None
        return lat, lon, tz_at(lat, lon), f"{lat:.2f}, {lon:.2f}", None
    found = geo.search(text, 6)
    if not found:
        await m.answer(t(lang, "place_not_found"))
        return None
    city = _auto(text, found)
    if city:
        await m.answer(t(lang, "place_found", city=city.label(lang)))
        return city.lat, city.lon, city.tz, city.label(lang), city.key
    kbd = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
        text=f"{c.label(lang)} · {_pop(c.pop, lang)}", callback_data=f"{prefix}:{c.key}")] for c in found])
    await m.answer(t(lang, "place_choose"), reply_markup=kbd)
    return None


def _pop(n: int, lang: str) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f} {'M' if lang == 'en' else 'млн'}".replace(".0 ", " ")
    if n >= 1000:
        return f"{n // 1000} {'k' if lang == 'en' else 'тыс.'}"
    return f"{n}"
