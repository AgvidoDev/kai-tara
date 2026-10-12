"""Строки интерфейса бота на разных языках.

t(lang, key, **kw) — строка по ключу; новый язык = ещё одно поле в каждой записи.
Язык пользователя определяется по Telegram при первом /start, меняется в настройках.
"""
from __future__ import annotations

from jyotish.texts import LANGS, norm

RU_FAMILY = {"ru", "uk", "be", "kk"}


def detect(language_code: str | None) -> str:
    code = (language_code or "").split("-")[0].lower()
    return "ru" if code in RU_FAMILY else "en"


def t(lang: str | None, key: str, **kw) -> str:
    s = M[key][norm(lang)]
    return s.format(**kw) if kw else s


def variants(key: str) -> set[str]:
    """Все языковые варианты строки — для фильтров по тексту кнопок."""
    return {M[key][lang] for lang in LANGS}


M: dict[str, dict[str, str]] = {
    # ------------------------------------------------------------ кнопки меню
    "btn_forecast": {"ru": "🔮 Прогноз", "en": "🔮 Forecast"},
    "btn_today": {"ru": "☀️ Сегодня", "en": "☀️ Today"},
    "btn_personal": {"ru": "👤 Личный прогноз", "en": "👤 Personal"},
    "btn_compat": {"ru": "💞 Совместимость", "en": "💞 Compatibility"},
    "btn_calendar": {"ru": "📅 Календарь", "en": "📅 Calendar"},
    "btn_premium": {"ru": "💎 Премиум", "en": "💎 Premium"},
    "btn_profile": {"ru": "🪐 Моя карта", "en": "🪐 My chart"},
    "btn_settings": {"ru": "⚙️ Настройки", "en": "⚙️ Settings"},
    # ------------------------------------------------------------ инлайн-кнопки
    "kb_consent": {"ru": "✅ Согласен на обработку данных", "en": "✅ I agree to data processing"},
    "kb_privacy": {"ru": "🔒 Политика конфиденциальности", "en": "🔒 Privacy policy"},
    "kb_time_unknown": {"ru": "Не знаю время", "en": "I don't know the time"},
    "kb_send_geo": {"ru": "📍 Отправить геолокацию", "en": "📍 Send location"},
    "kb_mode_moon": {"ru": "🌙 По Луне (классический джйотиш)", "en": "🌙 By Moon (classic Jyotish)"},
    "kb_mode_sid": {"ru": "☀️ По сидерическому Солнцу", "en": "☀️ By sidereal Sun"},
    "kb_mode_trop": {"ru": "♈ По привычному знаку", "en": "♈ By familiar sign"},
    "kb_set_mode": {"ru": "Режим знака", "en": "Sign mode"},
    "kb_set_city": {"ru": "Город для расчёта времени", "en": "City for event times"},
    "kb_set_daily": {"ru": "Утренний прогноз: {state}", "en": "Morning forecast: {state}"},
    "kb_on": {"ru": "вкл ✅", "en": "on ✅"},
    "kb_off": {"ru": "выкл", "en": "off"},
    "kb_set_lang": {"ru": "🌐 Язык: Русский", "en": "🌐 Language: English"},
    "kb_set_birth": {"ru": "Изменить данные рождения", "en": "Change birth data"},
    "kb_set_delete": {"ru": "🗑 Удалить мои данные", "en": "🗑 Delete my data"},
    "kb_male": {"ru": "Я мужчина", "en": "I'm a man"},
    "kb_female": {"ru": "Я женщина", "en": "I'm a woman"},
    "kb_del_yes": {"ru": "Да, удалить всё", "en": "Yes, delete everything"},
    "kb_cancel": {"ru": "Отмена", "en": "Cancel"},
    "kb_more": {"ru": "Подробнее ▾", "en": "More ▾"},
    "kb_all_glossary": {"ru": "📚 Весь словарь", "en": "📚 Full glossary"},
    "kb_sections": {"ru": "← Разделы", "en": "← Sections"},
    "kb_terms": {"ru": "📖 Термины этого прогноза", "en": "📖 Terms in this forecast"},
    "kb_transits": {"ru": "🐉 Большие транзиты", "en": "🐉 Major transits"},
    "kb_transit_personal": {"ru": "🔮 По моей натальной карте", "en": "🔮 From my birth chart"},
    "kb_what_for_me": {"ru": "Что это значит для меня", "en": "What it means for me"},
    "kb_buy_premium": {"ru": "💎 Премиум — {price} ⭐ / 30 дней", "en": "💎 Premium — {price} ⭐ / 30 days"},
    "kb_buy_compat": {"ru": "💞 Одна проверка — {price} ⭐", "en": "💞 One check — {price} ⭐"},
    "kb_ref": {"ru": "🎁 Получить Премиум за друга", "en": "🎁 Get Premium for a friend"},
    "kb_invite": {"ru": "🎁 Пригласить друга", "en": "🎁 Invite a friend"},
    "kb_sub_cancel": {"ru": "Отменить автопродление", "en": "Cancel auto-renewal"},
    "kb_sub_resume": {"ru": "Включить автопродление", "en": "Turn auto-renewal on"},
    # ------------------------------------------------------------ регистрация
    "consent": {
        "ru": "Привет! Я Кай Тара и делаю прогнозы по ведической астрологии (джйотиш).\n\n"
              "Для расчёта мне нужны дата, время и место рождения. Я использую их только для расчёта и "
              "<b>не храню</b> — сохраняются лишь вычисленные знаки (Солнце, Луна, лагна, планеты). "
              "Удалить всё можно в любой момент: ⚙️ Настройки → Удалить мои данные.\n\n"
              "Подтвердите согласие на обработку персональных данных.",
        "en": "Hi! I'm Kai Tara, and I make Vedic astrology (Jyotish) forecasts.\n\n"
              "To calculate them I need your date, time and place of birth. I use them only for the calculation "
              "and <b>don't store them</b> — only the computed signs are kept (Sun, Moon, Lagna, planets). "
              "You can delete everything at any time: ⚙️ Settings → Delete my data.\n\n"
              "Please confirm that you agree to the processing of your personal data.",
    },
    "welcome_back": {"ru": "С возвращением! Выберите действие.", "en": "Welcome back! Choose what you'd like."},
    "ask_date": {"ru": "Введите дату рождения в формате <b>ДД.ММ.ГГГГ</b>",
                 "en": "Enter your date of birth as <b>DD.MM.YYYY</b>"},
    "bad_date": {"ru": "Не понял дату. Пример: <b>14.05.1980</b>", "en": "I didn't get that date. Example: <b>14.05.1980</b>"},
    "ask_time": {"ru": "Время рождения <b>ЧЧ:ММ</b> (по местному времени места рождения).\n"
                       "Без времени нельзя точно определить знак Луны и лагну.",
                 "en": "Time of birth as <b>HH:MM</b> (local time at the place of birth).\n"
                       "Without it, the Moon sign and Lagna can't be determined precisely."},
    "bad_time": {"ru": "Формат времени: <b>06:30</b>. Или нажмите «Не знаю время».",
                 "en": "Time format: <b>06:30</b>. Or tap “I don't know the time”."},
    "ask_place": {"ru": "Место рождения: <b>напишите название города</b> (например <i>Казань</i>) "
                        "или выберите кнопкой.",
                  "en": "Place of birth: <b>type the name of the city</b> (for example <i>Manchester</i>) "
                        "or choose one below."},
    "place_hint": {"ru": "Знаю все города и посёлки России и СНГ от 1000 жителей и крупные города мира. "
                         "Можно и геолокацией.",
                   "en": "I know all towns in Russia and the CIS from 1,000 people and major cities worldwide. "
                         "You can also send a location."},
    "geo_label": {"ru": "геолокация", "en": "location"},
    "bad_coords": {"ru": "Не понял. Выберите город кнопкой или пришлите координаты: <code>55.75, 37.62</code>",
                   "en": "I didn't get that. Choose a city or send coordinates: <code>51.51, -0.13</code>"},
    "coords_range": {"ru": "Координаты вне диапазона.", "en": "Coordinates are out of range."},
    "done_profile": {"ru": "Готово! Ваша карта:\n\n{profile}\n\n🔒 Дату, время и место рождения я не храню — "
                           "только вычисленные знаки.",
                     "en": "Done! Your chart:\n\n{profile}\n\n🔒 I don't store your date, time or place of birth — "
                           "only the computed signs."},
    "ask_mode": {"ru": "По какому знаку присылать прогнозы?", "en": "Which sign should I use for your forecasts?"},
    "promo_welcome": {"ru": "🎁 До {until} все функции Премиума бесплатны: {b1}, {b2}, {b3}, {b4}. Пробуйте!\n\n"
                            "Непонятное слово в прогнозе — нажмите на него, и я объясню.",
                      "en": "🎁 Until {until} all Premium features are free: {b1}, {b2}, {b3}, {b4}. Try them!\n\n"
                            "Tap any unfamiliar word in a forecast and I'll explain it."},
    "trial_welcome": {"ru": "🎁 Дарим {days} дня Премиума: подробный прогноз {b1}, {b2}, {b3} и {b4}. Пробуйте!\n\n"
                            "Непонятное слово в прогнозе — нажмите на него, и я объясню.",
                      "en": "🎁 Here are {days} days of Premium: detailed {b1}, {b2}, {b3} and {b4}. Try them!\n\n"
                            "Tap any unfamiliar word in a forecast and I'll explain it."},
    "ref_joined": {"ru": "🎁 Ваш друг присоединился! +{days} дней Премиума.",
                   "en": "🎁 Your friend has joined! +{days} days of Premium."},
    # ------------------------------------------------------------ прогнозы и профиль
    "need_birth": {"ru": "Сначала введите данные рождения: /start", "en": "Please enter your birth data first: /start"},
    "moon_unknown_mode": {"ru": "Знак Луны не определён без времени рождения. Смените режим в ⚙️ Настройках.",
                          "en": "Your Moon sign can't be determined without a birth time. Change the mode in ⚙️ Settings."},
    "need_time_personal": {"ru": "Для личного прогноза нужно время рождения. ⚙️ Настройки → Изменить данные рождения.",
                           "en": "The personal forecast needs your birth time. ⚙️ Settings → Change birth data."},
    "no_data": {"ru": "Данных пока нет: /start", "en": "No data yet: /start"},
    "time_not_given": {"ru": "\n(время рождения не было указано)", "en": "\n(birth time was not given)"},
    "me_text": {"ru": "{profile}{tnote}\n\nРежим: {mode}\nГород расчёта: {city}\n\n"
                      "🔒 Дату, время и место рождения я не храню — только вычисленные знаки.",
                "en": "{profile}{tnote}\n\nMode: {mode}\nCity for event times: {city}\n\n"
                      "🔒 I don't store your date, time or place of birth — only the computed signs."},
    # ------------------------------------------------------------ настройки
    "settings": {"ru": "Настройки:", "en": "Settings:"},
    "daily_on": {"ru": "Утренний прогноз включён", "en": "Morning forecast is on"},
    "daily_off": {"ru": "Утренний прогноз выключен", "en": "Morning forecast is off"},
    "choose_mode": {"ru": "Выберите режим:", "en": "Choose a mode:"},
    "need_time_short": {"ru": "Нужно время рождения", "en": "Birth time needed"},
    "mode_set": {"ru": "Режим: {mode}. Ваш знак — <b>{sign}</b>.\nПрогноз: кнопка {btn}",
                 "en": "Mode: {mode}. Your sign is <b>{sign}</b>.\nForecast: the {btn} button"},
    "choose_city": {"ru": "Город, по времени которого считать события — напишите название или выберите кнопкой:",
                    "en": "Which city's time should I use for events? Type its name or choose below:"},
    "city_set": {"ru": "Город расчёта: <b>{city}</b>", "en": "City for event times: <b>{city}</b>"},
    "lang_set": {"ru": "Язык: русский 🇷🇺", "en": "Language: English 🇬🇧"},
    "delete_confirm": {"ru": "Удалить все ваши данные без возможности восстановления?",
                       "en": "Delete all your data permanently?"},
    "deleted": {"ru": "Данные удалены. Чтобы начать заново — /start", "en": "Your data has been deleted. To start again — /start"},
    "cancelled": {"ru": "Отменено.", "en": "Cancelled."},
    "help": {
        "ru": "/forecast — прогноз на текущий лунный месяц\n/today — прогноз на сегодня\n"
              "/week — 7 дней, /month — месяц 💎\n"
              "/personal — личный прогноз (даши, транзиты, упаи) 💎\n/calendar — благоприятные дни 💎\n"
              "/compat — совместимость пары\n/transits — большие транзиты (узлы, Юпитер, Сатурн)\n"
              "/chart — натальная карта (картинка и планеты)\n/glossary — словарь терминов\n/me — моя карта\n"
              "/premium — Премиум и приглашения\n/settings — режим знака, город, язык, рассылка, удаление данных\n"
              "/terms — условия, /privacy — конфиденциальность, /source — исходный код\n\n"
              "Любое подчёркнутое слово в прогнозе можно нажать — я объясню, что оно значит.",
        "en": "/forecast — forecast for the current lunar month\n/today — today's forecast\n"
              "/week — 7 days, /month — month 💎\n"
              "/personal — personal forecast (dashas, transits, upayas) 💎\n/calendar — favourable days 💎\n"
              "/compat — couple compatibility\n/transits — major transits (nodes, Jupiter, Saturn)\n"
              "/chart — birth chart (image and planets)\n/glossary — glossary of terms\n/me — my chart\n"
              "/premium — Premium and invitations\n/settings — sign mode, city, language, messages, delete data\n"
              "/terms — terms, /privacy — privacy, /source — source code\n\n"
              "Tap any underlined word in a forecast and I'll explain what it means.",
    },
    # ------------------------------------------------------------ разделы
    "feat_personal": {"ru": "Личный прогноз", "en": "Personal forecast"},
    "feat_calendar": {"ru": "Календарь благоприятных дней", "en": "Calendar of favourable days"},
    "feat_compat": {"ru": "Совместимость пары", "en": "Couple compatibility"},
    "feat_transit_personal": {"ru": "Личная версия большого транзита", "en": "Personal version of a major transit"},
    "counting": {"ru": "Считаю 30 дней…", "en": "Calculating 30 days…"},
    "compat_intro": {"ru": "💞 Проверим совместимость по ашта-куте — классической ведической системе (36 баллов).\n\n"
                           "Данные партнёра используются только для расчёта и не сохраняются.\n\n"
                           "Система различает роли мужчины и женщины. Кто вы?",
                     "en": "💞 Let's check compatibility with Ashta Kuta — the classical Vedic system (36 points).\n\n"
                           "Your partner's data is used only for the calculation and is not stored.\n\n"
                           "The system distinguishes the roles of man and woman. Who are you?"},
    "ask_p_date": {"ru": "Дата рождения партнёра <b>ДД.ММ.ГГГГ</b>:", "en": "Your partner's date of birth <b>DD.MM.YYYY</b>:"},
    "bad_p_date": {"ru": "Не понял дату. Пример: <b>02.03.1985</b>", "en": "I didn't get that date. Example: <b>02.03.1985</b>"},
    "ask_p_time": {"ru": "Время рождения партнёра <b>ЧЧ:ММ</b> (если известно):",
                   "en": "Your partner's time of birth <b>HH:MM</b> (if known):"},
    "ask_p_place": {"ru": "Город рождения партнёра — напишите название или выберите кнопкой:",
                    "en": "Your partner's city of birth — type its name or choose below:"},
    "bad_p_place": {"ru": "Выберите город кнопкой или пришлите координаты: <code>55.75, 37.62</code>",
                    "en": "Choose a city or send coordinates: <code>51.51, -0.13</code>"},
    "compat_need_moon": {"ru": "Чтобы посчитать совместимость, нужна точная накшатра вашей Луны — укажите "
                               "время рождения: ⚙️ Настройки → Изменить данные рождения.",
                         "en": "Compatibility needs your exact Moon nakshatra — please add your birth time: "
                               "⚙️ Settings → Change birth data."},
    "you": {"ru": "Вы", "en": "You"},
    "partner": {"ru": "Партнёр", "en": "Partner"},
    "warn_my": {"ru": "ваша накшатра Луны неточна без времени рождения",
                "en": "your Moon nakshatra is uncertain without a birth time"},
    "warn_p": {"ru": "накшатра Луны партнёра неточна без времени рождения",
               "en": "your partner's Moon nakshatra is uncertain without a birth time"},
    "warn_line": {"ru": "\n\n⚠️ Внимание: {items} — результат может отличаться на несколько баллов.",
                  "en": "\n\n⚠️ Note: {items} — the result may differ by a few points."},
    "compat_again": {"ru": "Ещё одна пара — кнопка {btn}", "en": "Another couple — the {btn} button"},
    "gloss_intro": {"ru": "📚 <b>Словарь джйотиш</b>\n\nВыберите раздел. А любое подчёркнутое слово в прогнозе "
                          "можно просто нажать.",
                    "en": "📚 <b>Jyotish glossary</b>\n\nChoose a section. Or just tap any underlined word in a forecast."},
    "gloss_choose": {"ru": "📚 <b>Словарь джйотиш</b> — выберите раздел:", "en": "📚 <b>Jyotish glossary</b> — choose a section:"},
    "term_missing": {"ru": "Такого термина нет в словаре. Весь словарь: /glossary",
                     "en": "That term isn't in the glossary. Full glossary: /glossary"},
    "term_not_found": {"ru": "Термин не найден", "en": "Term not found"},
    "no_terms": {"ru": "В этом сообщении нет терминов из словаря", "en": "There are no glossary terms in this message"},
    "terms_in_msg": {"ru": "📖 Термины из этого сообщения — нажмите, чтобы узнать значение:",
                     "en": "📖 Terms from this message — tap to see what they mean:"},
    "no_transits": {"ru": "Сейчас нет больших транзитов — сообщу, когда приблизится следующий.",
                    "en": "There are no major transits right now — I'll let you know when the next one approaches."},
    "transits_intro": {"ru": "🪐 <b>Большие транзиты</b> — события, которые задают фон на месяцы и годы. Выберите:",
                       "en": "🪐 <b>Major transits</b> — events that set the background for months and years. Choose:"},
    "transit_missing": {"ru": "Транзит не найден", "en": "Transit not found"},
    "no_data_short": {"ru": "Нет данных", "en": "No data"},
    # ------------------------------------------------------------ Премиум и оплата
    "premium_features": {
        "ru": "☀️ Подробный прогноз на каждый день + утренняя рассылка\n"
              "👤 Личный прогноз: даши, транзиты от лагны и Луны, упаи\n"
              "📅 Календарь благоприятных дней на 30 дней вперёд\n"
              "💞 Совместимость пар без ограничений\n"
              "🐉 Большие транзиты по вашей натальной карте",
        "en": "☀️ A detailed forecast every day + a morning message\n"
              "👤 Personal forecast: dashas, transits from the Lagna and Moon, upayas\n"
              "📅 A calendar of favourable days 30 days ahead\n"
              "💞 Unlimited couple compatibility\n"
              "🐉 Major transits from your birth chart",
    },
    "paywall": {"ru": "🔒 <b>{feature}</b> — в Премиуме.\n\n{features}", "en": "🔒 <b>{feature}</b> is a Premium feature.\n\n{features}"},
    "premium_title": {"ru": "💎 <b>Астро Премиум</b>", "en": "💎 <b>Astro Premium</b>"},
    "promo_line": {"ru": "🎁 До {until} все функции Премиума бесплатны для всех.",
                   "en": "🎁 Until {until} all Premium features are free for everyone."},
    "source": {"ru": "🧩 Исходный код Kai Tara открыт (лицензия AGPL-3.0):\n{url}\n\n"
                     "Ваши данные в коде не публикуются — они хранятся только в базе бота.",
               "en": "🧩 Kai Tara is open source (AGPL-3.0):\n{url}\n\n"
                     "Your data is not part of the code — it is kept only in the bot's database."},
    "source_soon": {"ru": "🧩 Исходный код Kai Tara распространяется по лицензии AGPL-3.0. Ссылка на репозиторий "
                          "появится здесь в ближайшее время.",
                    "en": "🧩 Kai Tara's source code is licensed under AGPL-3.0. The repository link will appear "
                          "here shortly."},
    "kb_why": {"ru": "❓ Почему так?", "en": "❓ Why?"},
    "kb_ics": {"ru": "📥 В календарь телефона", "en": "📥 Add to phone calendar"},
    "feat_ics": {"ru": "Астрокалендарь для телефона", "en": "Astro calendar for your phone"},
    "ics_caption": {"ru": "📥 Астрокалендарь на 90 дней: откройте файл — события добавятся в календарь "
                          "телефона (Google, Apple, Outlook).",
                    "en": "📥 Astro calendar for 90 days: open the file and the events will be added to your "
                          "phone calendar (Google, Apple, Outlook)."},
    "cmd_ics": {"ru": "Астрокалендарь в телефон", "en": "Astro calendar for phone"},
    "kb_pdf30": {"ru": "📄 PDF на 30 дней", "en": "📄 30-day PDF"},
    "feat_pdf30": {"ru": "Персональный прогноз на 30 дней (PDF)", "en": "Personal 30-day forecast (PDF)"},
    "pdf30_caption": {"ru": "📄 Ваш прогноз на 30 дней · Кай Тара", "en": "📄 Your 30-day forecast · Kai Tara"},
    "cmd_pdf30": {"ru": "Прогноз на 30 дней (PDF)", "en": "30-day forecast (PDF)"},
    "kb_week": {"ru": "📆 7 дней", "en": "📆 7 days"},
    "kb_month": {"ru": "🗓 Месяц", "en": "🗓 Month"},
    "feat_week": {"ru": "Прогноз на 7 дней", "en": "7-day forecast"},
    "feat_month": {"ru": "Прогноз на месяц", "en": "Month forecast"},
    "cmd_week": {"ru": "Прогноз на 7 дней", "en": "7-day forecast"},
    "cmd_month": {"ru": "Прогноз на месяц", "en": "Month forecast"},
    "free_line": {"ru": "🎁 Сейчас все функции Премиума бесплатны для всех.",
                  "en": "🎁 Right now all Premium features are free for everyone."},
    "free_welcome": {"ru": "🎁 Все функции Премиума сейчас бесплатны: {b1}, {b2}, {b3}, {b4}. Пробуйте!\n\n"
                           "Непонятное слово в прогнозе — нажмите на него, и я объясню.",
                     "en": "🎁 All Premium features are free right now: {b1}, {b2}, {b3}, {b4}. Try them!\n\n"
                           "Tap any unfamiliar word in a forecast and I'll explain it."},
    "promo_no_pay": {"ru": "Оплата не нужна — просто пользуйтесь.", "en": "No payment needed — just enjoy."},
    "terms_link": {"ru": "Условия: /terms · Конфиденциальность: /privacy", "en": "Terms: /terms · Privacy: /privacy"},
    "status_admin": {"ru": "Статус: администратор — все функции открыты.", "en": "Status: administrator — everything is unlocked."},
    "status_active": {"ru": "Статус: <b>активен до {until}</b>", "en": "Status: <b>active until {until}</b>"},
    "renew_on": {"ru": "Автопродление включено.", "en": "Auto-renewal is on."},
    "renew_off": {"ru": "Автопродление отключено.", "en": "Auto-renewal is off."},
    "price_line": {"ru": "Стоимость: <b>{price} ⭐ за 30 дней</b>, автопродление, отмена в один клик.",
                   "en": "Price: <b>{price} ⭐ for 30 days</b>, auto-renewal, cancel with one tap."},
    "credits": {"ru": "Проверок совместимости в запасе: {n}", "en": "Compatibility checks left: {n}"},
    "invite_line": {"ru": "🎁 Пригласите друга — получите {days} дней Премиума, когда он введёт данные рождения.",
                    "en": "🎁 Invite a friend — get {days} days of Premium when they enter their birth data."},
    "ref_text": {"ru": "🎁 Ваша ссылка для друзей:\n{link}\n\nЗа каждого друга, который зарегистрируется и введёт "
                       "данные рождения, — {days} дней Премиума. Уже приглашено: {n}.",
                 "en": "🎁 Your link for friends:\n{link}\n\nFor every friend who signs up and enters their birth data "
                       "you get {days} days of Premium. Invited so far: {n}."},
    "sub_not_found": {"ru": "Подписка не найдена", "en": "Subscription not found"},
    "sub_error": {"ru": "Не удалось изменить подписку. Попробуйте в настройках Telegram.",
                  "en": "Couldn't change the subscription. Try in Telegram settings."},
    "sub_cancelled": {"ru": "Автопродление отключено. Премиум действует до {until}.",
                      "en": "Auto-renewal is off. Premium stays active until {until}."},
    "sub_resumed": {"ru": "Автопродление снова включено.", "en": "Auto-renewal is back on."},
    "inv_sub_title": {"ru": "Астро Премиум — 30 дней", "en": "Astro Premium — 30 days"},
    "inv_sub_desc": {"ru": "Ежедневный личный прогноз, календарь благоприятных дней, совместимость, упаи.",
                     "en": "Daily personal forecast, calendar of favourable days, compatibility, upayas."},
    "inv_sub_label": {"ru": "Премиум на 30 дней", "en": "Premium for 30 days"},
    "inv_compat_title": {"ru": "Совместимость пары", "en": "Couple compatibility"},
    "inv_compat_desc": {"ru": "Одна проверка по ашта-куте: 8 критериев, 36 баллов.",
                        "en": "One Ashta Kuta check: 8 criteria, 36 points."},
    "inv_compat_label": {"ru": "Проверка совместимости", "en": "Compatibility check"},
    "price_changed": {"ru": "Цена изменилась — откройте 💎 Премиум заново.", "en": "The price has changed — open 💎 Premium again."},
    "paid_first": {"ru": "💎 Спасибо! Премиум активирован до {until}.\n\nПопробуйте: {b1}, {b2}, {b3}.",
                   "en": "💎 Thank you! Premium is active until {until}.\n\nTry: {b1}, {b2}, {b3}."},
    "paid_renew": {"ru": "💎 Премиум продлён до {until}.", "en": "💎 Premium renewed until {until}."},
    "paid_compat": {"ru": "Оплачено! Нажмите {btn}, чтобы ввести данные партнёра.",
                    "en": "Paid! Tap {btn} to enter your partner's details."},
    "paysupport_usage": {"ru": "Опишите вопрос по оплате одним сообщением после команды, например:\n"
                               "<code>/paysupport оплатил, но Премиум не включился</code>",
                         "en": "Describe your payment question in one message after the command, for example:\n"
                               "<code>/paysupport I paid but Premium didn't turn on</code>"},
    "paysupport_ok": {"ru": "Сообщение передано в поддержку. Ответим в этом чате.",
                      "en": "Your message has been passed to support. We'll reply in this chat."},
    "terms": {
        "ru": "<b>Условия использования</b>\n\n"
              "1. Бот предоставляет астрологические прогнозы по ведической традиции. Прогнозы носят "
              "ознакомительный характер и не являются медицинской, финансовой или юридической консультацией.\n"
              "2. Премиум оплачивается в Telegram Stars и продлевается автоматически каждые 30 дней, пока вы "
              "не отмените подписку (💎 Премиум → «Отменить автопродление» или в настройках Telegram). "
              "После отмены доступ сохраняется до конца оплаченного периода.\n"
              "3. Разовая покупка «Совместимость» даёт одну проверку пары.\n"
              "4. Возврат возможен, если услуга не была оказана из-за технической ошибки: /paysupport.\n"
              "5. Дату, время и место рождения бот не хранит — только вычисленные астрологические знаки. "
              "Данные партнёра для совместимости не сохраняются. Подробнее: /privacy\n"
              "6. Данные о городах: GeoNames (geonames.org), лицензия CC BY 4.0.\n"
              "7. Исходный код бота открыт по лицензии AGPL-3.0: /source",
        "en": "<b>Terms of use</b>\n\n"
              "1. The bot provides astrological forecasts in the Vedic tradition. Forecasts are for information "
              "only and are not medical, financial or legal advice.\n"
              "2. Premium is paid in Telegram Stars and renews automatically every 30 days until you cancel "
              "(💎 Premium → “Cancel auto-renewal” or in Telegram settings). After cancelling, access continues "
              "until the end of the paid period.\n"
              "3. A one-off “Compatibility” purchase gives one couple check.\n"
              "4. Refunds are possible if the service wasn't delivered because of a technical error: /paysupport.\n"
              "5. The bot does not store your date, time or place of birth — only the computed astrological signs. "
              "Your partner's data for compatibility is not stored. Details: /privacy\n"
              "6. City data: GeoNames (geonames.org), licensed under CC BY 4.0.\n"
              "7. The bot's source code is open under AGPL-3.0: /source",
    },
    "privacy": {
        "ru": "<b>Политика конфиденциальности</b>\n\n"
              "<b>Что я храню:</b> ваш Telegram ID, язык, выбранный город и режим знака, согласие на обработку "
              "данных и вычисленный астрологический профиль (знаки Солнца, Луны, лагны и планет, накшатра Луны, "
              "периоды даш с точностью до месяца), а также сведения об оплатах.\n"
              "<b>Чего я не храню:</b> дату, время и место рождения — они используются только в момент расчёта "
              "и в базу не записываются. Для натальной карты они держатся в оперативной памяти бота не дольше "
              "30 минут (чтобы успеть получить PDF-разбор), затем стираются. Данные партнёра для совместимости "
              "не сохраняются.\n"
              "<b>Зачем:</b> чтобы присылать прогнозы и рассылки, которые вы выбрали.\n"
              "<b>Где:</b> на сервере в ЕС. Данные никому не передаются и не продаются.\n"
              "<b>Ваши права:</b> удалить все данные можно в любой момент: ⚙️ Настройки → Удалить мои данные. "
              "Сведения об оплатах сохраняются для учёта и возвратов. Вопросы — /paysupport.",
        "en": "<b>Privacy policy</b>\n\n"
              "<b>What I store:</b> your Telegram ID, language, chosen city and sign mode, your consent, and the "
              "computed astrological profile (signs of the Sun, Moon, Lagna and planets, Moon nakshatra, dasha "
              "periods to the month), plus payment records.\n"
              "<b>What I don't store:</b> your date, time and place of birth — they are used only at the moment of "
              "calculation and never written to the database. For a birth chart they stay in the bot's working "
              "memory for at most 30 minutes (so you can get the PDF reading), then they are wiped. Your partner's "
              "data for compatibility is not stored.\n"
              "<b>Why:</b> to send you the forecasts and messages you chose.\n"
              "<b>Where:</b> on a server in the EU. Data is never shared or sold.\n"
              "<b>Your rights:</b> you can delete all your data at any time: ⚙️ Settings → Delete my data. "
              "Payment records are kept for accounting and refunds. Questions — /paysupport.",
    },
    # ------------------------------------------------------------ натальная карта
    "kb_chart": {"ru": "🗺 Построить натальную карту", "en": "🗺 Build my birth chart"},
    "chart_intro": {"ru": "🗺 <b>Натальная карта</b>\n\nДата, время и место рождения нужны только для этого "
                          "расчёта — я их не сохраняю.\n\nВведите дату рождения <b>ДД.ММ.ГГГГ</b>:",
                    "en": "🗺 <b>Birth chart</b>\n\nYour date, time and place of birth are used only for this "
                          "calculation — I don't save them.\n\nEnter your date of birth <b>DD.MM.YYYY</b>:"},
    "chart_caption": {"ru": "🗺 Натальная карта · Кай Тара", "en": "🗺 Birth chart · Kai Tara"},
    "chart_again": {"ru": "Построить ещё одну карту (например, для близкого) — /chart",
                    "en": "Build another chart (for someone close, say) — /chart"},
    "cmd_chart": {"ru": "Натальная карта", "en": "Birth chart"},
    # ------------------------------------------------------------ поиск города
    "place_not_found": {"ru": "Не нашёл такой город. Проверьте написание, напишите крупный город рядом "
                              "или пришлите геолокацию / координаты (<code>55.75, 37.62</code>).",
                        "en": "I couldn't find that city. Check the spelling, try a larger city nearby, "
                              "or send a location / coordinates (<code>51.51, -0.13</code>)."},
    "place_found": {"ru": "📍 {city}", "en": "📍 {city}"},
    "place_choose": {"ru": "Нашёл несколько городов — выберите ваш. Если нужного нет, уточните регион через "
                           "запятую: <i>Октябрьский, Пермский</i>",
                     "en": "I found several places — choose yours. If it's not listed, add the region after a "
                           "comma: <i>Springfield, Illinois</i>"},
    # ------------------------------------------------------------ PDF-разбор
    "kb_report_paid": {"ru": "📄 Полный разбор (PDF) — {price} ⭐", "en": "📄 Full reading (PDF) — {price} ⭐"},
    "kb_report_free": {"ru": "📄 Полный разбор (PDF)", "en": "📄 Full reading (PDF)"},
    "report_expired": {"ru": "Данные карты уже стёрты из памяти — я держу их не дольше 30 минут. "
                             "Постройте карту заново: /chart",
                       "en": "The chart data has already been wiped from memory — I keep it for 30 minutes at most. "
                             "Please build the chart again: /chart"},
    "report_making": {"ru": "Готовлю разбор…", "en": "Preparing your reading…"},
    "report_caption": {"ru": "📄 Разбор натальной карты · Кай Тара", "en": "📄 Birth chart reading · Kai Tara"},
    "report_pending": {"ru": "Оплата получена. Постройте карту (/chart) — разбор придёт сразу после неё.",
                       "en": "Payment received. Build your chart (/chart) — the reading will follow right after."},
    "inv_report_title": {"ru": "Разбор натальной карты", "en": "Birth chart reading"},
    "inv_report_desc": {"ru": "PDF: лагна, Луна и накшатра, все планеты и дома, йоги, даши, упаи.",
                        "en": "PDF: Lagna, Moon and nakshatra, all planets and houses, yogas, dashas, upayas."},
    "inv_report_label": {"ru": "PDF-разбор карты", "en": "PDF chart reading"},
    "report_credits": {"ru": "Оплаченных разборов карты: {n}", "en": "Paid chart readings left: {n}"},
    # ------------------------------------------------------------ команды меню
    "cmd_forecast": {"ru": "Прогноз на лунный месяц", "en": "Lunar month forecast"},
    "cmd_today": {"ru": "Прогноз на сегодня", "en": "Today's forecast"},
    "cmd_personal": {"ru": "Личный прогноз", "en": "Personal forecast"},
    "cmd_compat": {"ru": "Совместимость пары", "en": "Couple compatibility"},
    "cmd_calendar": {"ru": "Благоприятные дни", "en": "Favourable days"},
    "cmd_transits": {"ru": "Большие транзиты: узлы, Юпитер, Сатурн", "en": "Major transits: nodes, Jupiter, Saturn"},
    "cmd_glossary": {"ru": "Словарь терминов", "en": "Glossary"},
    "cmd_premium": {"ru": "Премиум и приглашения", "en": "Premium and invitations"},
    "cmd_me": {"ru": "Моя карта", "en": "My chart"},
    "cmd_settings": {"ru": "Настройки", "en": "Settings"},
    "cmd_help": {"ru": "Помощь", "en": "Help"},
}
