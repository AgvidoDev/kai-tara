"""Бренд «Кай Тара»: имя и описания бота на разных языках.

Telegram показывает пользователю версию на языке его приложения; для остальных языков —
версию без language_code (у нас английская). Выставляется при старте бота, только если
отличается: смена имени ограничена по частоте.
"""
from __future__ import annotations

import logging

from aiogram import Bot

log = logging.getLogger("branding")

PERSONA = "Кай Тара"
PERSONA_LATIN = "Kai Tara"

# language_code -> (имя ≤64, короткое описание ≤120, описание ≤512). "" — по умолчанию.
BRAND: dict[str, tuple[str, str, str]] = {
    "": (
        "Kai Tara — Horoscope & Astrology",
        "Vedic astrology by Kai Tara: daily horoscope, lucky days, compatibility, personal forecast.",
        "Hi, I'm Kai Tara — your guide to Vedic astrology (Jyotish).\n\n"
        "🔮 Forecasts for new and full moons for your sign\n"
        "☀️ Daily horoscope based on your Moon\n"
        "📅 Calendar of favourable days\n"
        "💞 Compatibility for couples (36-point Ashta-Kuta)\n"
        "👤 Personal forecast from your birth chart\n\n"
        "Tap any unfamiliar word in a forecast and I'll explain it. Press Start!",
    ),
    "ru": (
        "Кай Тара — гороскоп и астрология",
        "Ведическая астрология от Кай Тары: гороскоп на день, благоприятные дни, совместимость, личный прогноз.",
        "Привет! Я Кай Тара — проводник в ведическую астрологию (джйотиш).\n\n"
        "🔮 Прогнозы на новолуние и полнолуние для вашего знака\n"
        "☀️ Гороскоп на каждый день по вашей Луне\n"
        "📅 Календарь благоприятных дней\n"
        "💞 Совместимость пары (ашта-кута, 36 баллов)\n"
        "👤 Личный прогноз по натальной карте\n\n"
        "Любое непонятное слово в прогнозе можно нажать — я объясню. Жмите «Старт»!",
    ),
    "en": None,  # заполняется ниже копией варианта по умолчанию
    "fr": (
        "Kai Tara — Horoscope & Astrologie",
        "Astrologie védique avec Kai Tara : horoscope du jour, jours favorables, compatibilité, prévisions.",
        "Bonjour, je suis Kai Tara — votre guide de l'astrologie védique (Jyotish).\n\n"
        "🔮 Prévisions de nouvelle et pleine lune pour votre signe\n"
        "☀️ Horoscope du jour selon votre Lune\n"
        "📅 Calendrier des jours favorables\n"
        "💞 Compatibilité du couple (Ashta-Kuta, 36 points)\n"
        "👤 Prévisions personnelles d'après votre thème natal\n\n"
        "Touchez un mot inconnu dans une prévision et je vous l'explique. Appuyez sur Démarrer !",
    ),
    "es": (
        "Kai Tara — Horóscopo y Astrología",
        "Astrología védica con Kai Tara: horóscopo diario, días favorables, compatibilidad, pronóstico personal.",
        "Hola, soy Kai Tara, tu guía en la astrología védica (Jyotish).\n\n"
        "🔮 Pronósticos de luna nueva y luna llena para tu signo\n"
        "☀️ Horóscopo diario según tu Luna\n"
        "📅 Calendario de días favorables\n"
        "💞 Compatibilidad de pareja (Ashta-Kuta, 36 puntos)\n"
        "👤 Pronóstico personal según tu carta natal\n\n"
        "Toca cualquier palabra desconocida y te la explico. ¡Pulsa Iniciar!",
    ),
    "de": (
        "Kai Tara — Horoskop & Astrologie",
        "Vedische Astrologie mit Kai Tara: Tageshoroskop, günstige Tage, Partnerschaft, persönliche Prognose.",
        "Hallo, ich bin Kai Tara — dein Begleiter in der vedischen Astrologie (Jyotish).\n\n"
        "🔮 Prognosen zu Neumond und Vollmond für dein Zeichen\n"
        "☀️ Tageshoroskop nach deinem Mond\n"
        "📅 Kalender der günstigen Tage\n"
        "💞 Partnerschaftsvergleich (Ashta-Kuta, 36 Punkte)\n"
        "👤 Persönliche Prognose nach deinem Geburtshoroskop\n\n"
        "Tippe auf ein unbekanntes Wort, und ich erkläre es dir. Drück auf Starten!",
    ),
    "it": (
        "Kai Tara — Oroscopo e Astrologia",
        "Astrologia vedica con Kai Tara: oroscopo del giorno, giorni favorevoli, affinità di coppia, previsioni.",
        "Ciao, sono Kai Tara, la tua guida nell'astrologia vedica (Jyotish).\n\n"
        "🔮 Previsioni di luna nuova e luna piena per il tuo segno\n"
        "☀️ Oroscopo del giorno secondo la tua Luna\n"
        "📅 Calendario dei giorni favorevoli\n"
        "💞 Affinità di coppia (Ashta-Kuta, 36 punti)\n"
        "👤 Previsioni personali dal tuo tema natale\n\n"
        "Tocca una parola sconosciuta e te la spiego. Premi Avvia!",
    ),
}
BRAND["en"] = BRAND[""]


async def apply_branding(bot: Bot) -> None:
    """Выставляет имя и описания; ошибки не валят бота (например, лимит частоты на смену имени)."""
    for lang, (name, short, desc) in BRAND.items():
        code = lang or None
        try:
            if (await bot.get_my_name(language_code=code)).name != name:
                await bot.set_my_name(name=name, language_code=code)
            if (await bot.get_my_short_description(language_code=code)).short_description != short:
                await bot.set_my_short_description(short_description=short, language_code=code)
            if (await bot.get_my_description(language_code=code)).description != desc:
                await bot.set_my_description(description=desc, language_code=code)
        except Exception as e:
            log.warning("брендинг [%s] не применён: %s", lang or "default", e)
