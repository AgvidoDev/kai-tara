"""Словарь в боте: ссылки на термины в тексте прогноза и карточки терминов (на языке пользователя)."""
from __future__ import annotations

import re
from html import escape

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from jyotish.glossary import by_category, categories, matches, terms

from .i18n import t as tr

BOT_USERNAME: str | None = None    # выставляется в main.py после bot.me()
MAX_TERM_BUTTONS = 24

_TAG = re.compile(r"(<[^>]+>)")


def deeplink(key: str, username: str) -> str:
    return f"https://t.me/{username}?start=g_{key}"


def linkify(html: str, username: str | None = None, lang: str = "ru") -> str:
    """Первое вхождение каждого термина превращает в ссылку на карточку.

    Работает только по текстовым кускам между тегами и не заходит внутрь существующих <a>."""
    username = username or BOT_USERNAME
    if not username:
        return html
    parts = _TAG.split(html)
    used: set[str] = set()
    in_a = 0
    for i, part in enumerate(parts):
        if i % 2:           # тег
            low = part.lower()
            if low.startswith("<a ") or low == "<a>":
                in_a += 1
            elif low.startswith("</a"):
                in_a = max(0, in_a - 1)
            continue
        if in_a or not part:
            continue
        out, pos = [], 0
        for s, e, key in matches(part, lang):
            if key in used or _inside_entity(part, s):
                continue
            used.add(key)
            out += [part[pos:s], f'<a href="{deeplink(key, username)}">', part[s:e], "</a>"]
            pos = e
        out.append(part[pos:])
        parts[i] = "".join(out)
    return "".join(parts)


def _inside_entity(text: str, pos: int) -> bool:
    amp = text.rfind("&", 0, pos)
    return amp != -1 and ";" not in text[amp:pos] and re.match(r"&#?\w*$", text[amp:pos]) is not None


def card(key: str, full: bool = False, lang: str = "ru") -> tuple[str, InlineKeyboardMarkup]:
    T = terms(lang)
    term = T[key]
    body = term.short + (f"\n\n{term.long}" if full and term.long else "")
    text = f"📖 <b>{escape(term.title)}</b>\n\n{escape(body)}"
    rows = []
    if term.long and not full:
        rows.append([InlineKeyboardButton(text=tr(lang, "kb_more"), callback_data=f"glm:{key}")])
    rel = [InlineKeyboardButton(text=T[r].title, callback_data=f"gl:{r}") for r in term.related[:4] if r in T]
    rows += [rel[i:i + 2] for i in range(0, len(rel), 2)]
    rows.append([InlineKeyboardButton(text=tr(lang, "kb_all_glossary"), callback_data="glcat")])
    return text, InlineKeyboardMarkup(inline_keyboard=rows)


def terms_keyboard(keys: list[str], lang: str = "ru") -> InlineKeyboardMarkup:
    T = terms(lang)
    btn = [InlineKeyboardButton(text=T[k].title, callback_data=f"gl:{k}") for k in keys[:MAX_TERM_BUTTONS]]
    return InlineKeyboardMarkup(inline_keyboard=[btn[i:i + 2] for i in range(0, len(btn), 2)])


def categories_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    btn = [InlineKeyboardButton(text=name, callback_data=f"glc:{cat}") for cat, name in categories(lang).items()]
    return InlineKeyboardMarkup(inline_keyboard=[btn[i:i + 2] for i in range(0, len(btn), 2)])


def category_keyboard(cat: str, lang: str = "ru") -> InlineKeyboardMarkup:
    btn = [InlineKeyboardButton(text=x.title.removeprefix("Накшатра ").removesuffix(" nakshatra"),
                                callback_data=f"gl:{x.key}") for x in by_category(cat, lang)]
    width = 3 if len(btn) > 12 else 2
    rows = [btn[i:i + width] for i in range(0, len(btn), width)]
    rows.append([InlineKeyboardButton(text=tr(lang, "kb_sections"), callback_data="glcat")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def terms_button(lang: str = "ru") -> InlineKeyboardButton:
    return InlineKeyboardButton(text=tr(lang, "kb_terms"), callback_data="gll")


TERMS_BUTTON = terms_button("ru")   # обратная совместимость
