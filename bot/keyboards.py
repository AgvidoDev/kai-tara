from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton,
                           ReplyKeyboardMarkup, ReplyKeyboardRemove)

from jyotish.core import CITY_MENU, city_name

from .i18n import t, variants

# Тексты кнопок главного меню на всех языках — для фильтров F.text.in_(...)
BTN_FORECAST = variants("btn_forecast")
BTN_PERSONAL = variants("btn_personal")
BTN_SETTINGS = variants("btn_settings")
BTN_PROFILE = variants("btn_profile")
BTN_TODAY = variants("btn_today")
BTN_COMPAT = variants("btn_compat")
BTN_CALENDAR = variants("btn_calendar")
BTN_PREMIUM = variants("btn_premium")
BTN_FAMILY = variants("btn_family")
SHOW_PREMIUM = True          # в бесплатном режиме (FREE_MODE) кнопки «Премиум» в меню нет

remove = ReplyKeyboardRemove()


def main_menu(lang: str) -> ReplyKeyboardMarkup:
    b = lambda k: KeyboardButton(text=t(lang, k))  # noqa: E731
    last = [b("btn_profile"), b("btn_premium"), b("btn_settings")] if SHOW_PREMIUM else         [b("btn_profile"), b("btn_settings")]
    return ReplyKeyboardMarkup(keyboard=[[b("btn_forecast"), b("btn_today")],
                                         [b("btn_personal"), b("btn_compat")],
                                         [b("btn_calendar"), b("btn_family")],
                                         last], resize_keyboard=True)


def _inline(rows) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=txt, callback_data=cd) for txt, cd in r]
                                                 for r in rows])


def consent(lang: str) -> InlineKeyboardMarkup:
    return _inline([[(t(lang, "kb_consent"), "consent:yes")], [(t(lang, "kb_privacy"), "privacy")]])


def time_unknown(lang: str) -> InlineKeyboardMarkup:
    return _inline([[(t(lang, "kb_time_unknown"), "time:unknown")]])


def partner_time_unknown(lang: str) -> InlineKeyboardMarkup:
    return _inline([[(t(lang, "kb_time_unknown"), "ptime:unknown")]])


def place_reply(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=t(lang, "kb_send_geo"), request_location=True)]],
                               resize_keyboard=True, one_time_keyboard=True)


def cities(prefix: str, lang: str = "ru") -> InlineKeyboardMarkup:
    keys = CITY_MENU.get(lang, CITY_MENU["ru"])
    btn = [(city_name(k, lang), f"{prefix}:{k}") for k in keys]
    return _inline([btn[i:i + 2] for i in range(0, len(btn), 2)])


def modes(moon_available: bool, lang: str = "ru") -> InlineKeyboardMarkup:
    rows = []
    if moon_available:
        rows.append([(t(lang, "kb_mode_moon"), "mode:moon")])
    rows += [[(t(lang, "kb_mode_sid"), "mode:sun_sid")], [(t(lang, "kb_mode_trop"), "mode:sun_trop")]]
    return _inline(rows)


def settings(daily_push: bool = True, lang: str = "ru") -> InlineKeyboardMarkup:
    state = t(lang, "kb_on" if daily_push else "kb_off")
    return _inline([
        [(t(lang, "kb_set_mode"), "set:mode")],
        [(t(lang, "kb_set_city"), "set:city")],
        [(t(lang, "kb_set_daily", state=state), "set:daily")],
        [(t(lang, "kb_set_lang"), "set:lang")],
        [(t(lang, "kb_set_birth"), "set:birth")],
        [(t(lang, "kb_set_delete"), "set:delete")],
    ])


def languages() -> InlineKeyboardMarkup:
    return _inline([[("🇷🇺 Русский", "lang:ru"), ("🇬🇧 English", "lang:en")]])


def gender(lang: str = "ru") -> InlineKeyboardMarkup:
    return _inline([[(t(lang, "kb_male"), "cg:m"), (t(lang, "kb_female"), "cg:f")]])


def confirm_delete(lang: str = "ru") -> InlineKeyboardMarkup:
    return _inline([[(t(lang, "kb_del_yes"), "del:yes"), (t(lang, "kb_cancel"), "del:no")]])
