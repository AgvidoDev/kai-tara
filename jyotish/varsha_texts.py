"""Тексты годового прогноза (Варшапхала), ru/en. Шаблоны, без генерации."""
from __future__ import annotations

SECTION = {
    "ru": {
        "title": "Годовой прогноз (Варшапхала)", "for": "Подготовлено Кай Тарой",
        "year": "Год жизни {n}: {start} – {end}", "main": "Главное о годе", "lagna": "Лагна года",
        "muntha": "Мунтха — фокус года", "lords": "Управители года", "planets": "Планеты в карте года",
        "mudda": "Мудда-даша — периоды года", "transits": "Смены знаков медленных планет",
        "about": "О расчёте", "now": "сейчас", "no_transits": "За этот год Юпитер, Сатурн и Раху знак не меняют.",
        "solar": "Соляр (возвращение Солнца в натальную точку): {when}.",
        "no_time": "Время рождения не указано: лагна года неизвестна, дома считаются от натальной Луны, "
                   "мунтха — от знака Луны.",
        "lagna_lord": "Управитель лагны года — {planet}, в {h}-м доме года: темы «{theme}» выходят на первый план.",
        "muntha_lord": "Управитель мунтхи — {planet}, в {h}-м доме года: через темы «{theme}» реализуется главный "
                       "фокус года.",
        "planet_line": "{planet} — {sign}, {h}-й дом года ({theme}).",
        "mudda_line": "{lord}: {start} – {end}", "muntha_short": "Мунтха: {sign}, {h}-й дом года",
        "retro": " Попятное движение: возвращение к темам прошлого знака.",
        "ingress": "{date}: {planet} переходит в знак {sign} — {h}-й дом года ({theme}).",
        "method": "Таджика (Варшапхала): соляр по сидерическому Солнцу (айанамша Лахири), дома по целым знакам, "
                  "лагна года — для места рождения. Мунтха = знак лагны рождения + число полных лет. Мудда-даша — "
                  "Вимшоттари, сжатая в один год. Базовый уровень: без сахам и таджика-йог. Прогноз носит "
                  "ознакомительный характер. Данные рождения не сохраняются.",
        "quality": {"good": "благоприятная позиция", "ok": "умеренно благоприятная позиция",
                    "hard": "позиция, требующая осторожности"},
    },
    "en": {
        "title": "Annual forecast (Varshaphala)", "for": "Prepared by Kai Tara",
        "year": "Year of life {n}: {start} – {end}", "main": "The year at a glance", "lagna": "Ascendant of the year",
        "muntha": "Muntha — the focus of the year", "lords": "Lords of the year", "planets": "Planets in the year chart",
        "mudda": "Mudda dasha — periods of the year", "transits": "Sign changes of the slow planets",
        "about": "About the calculation", "now": "now",
        "no_transits": "Jupiter, Saturn and Rahu do not change signs this year.",
        "solar": "Solar return (the Sun back at its natal point): {when}.",
        "no_time": "Birth time not given: the ascendant of the year is unknown, houses are counted from the natal "
                   "Moon and the Muntha from the Moon sign.",
        "lagna_lord": "The lord of the year's ascendant is {planet}, in the {h} house of the year: the themes of "
                      "“{theme}” come to the fore.",
        "muntha_lord": "The lord of the Muntha is {planet}, in the {h} house of the year: the main focus of the year "
                       "works through “{theme}”.",
        "planet_line": "{planet} — {sign}, {h} house of the year ({theme}).",
        "mudda_line": "{lord}: {start} – {end}", "muntha_short": "Muntha: {sign}, {h} house of the year",
        "retro": " Retrograde motion: a return to the themes of the previous sign.",
        "ingress": "{date}: {planet} enters {sign} — the {h} house of the year ({theme}).",
        "method": "Tajika (Varshaphala): solar return of the sidereal Sun (Lahiri ayanamsha), whole-sign houses, "
                  "the year's ascendant for the birthplace. Muntha = birth ascendant sign + completed years. Mudda "
                  "dasha is Vimshottari compressed into one year. Basic level: no Sahams or Tajika yogas. This "
                  "forecast is for information only. Birth data is not stored.",
        "quality": {"good": "a favourable position", "ok": "a moderately favourable position",
                    "hard": "a position that calls for care"},
    },
}

# Мунтха в доме года (от лагны года)
MUNTHA = {
    "ru": [
        "Мунтха в 1-м доме: год о вас самих — новый старт, забота о здоровье и внешности, рост уверенности.",
        "Мунтха во 2-м доме: в фокусе деньги, семья и речь; хороший год, чтобы наладить финансы и копить.",
        "Мунтха в 3-м доме: год смелых шагов, поездок, учёбы и общения; удача приходит через собственные усилия.",
        "Мунтха в 4-м доме: в центре дом, мать, недвижимость и внутренний покой; возможны хлопоты по хозяйству — "
        "берегите душевное равновесие.",
        "Мунтха в 5-м доме: творчество, дети, учёба и романтика; удачный год для идей и обучения.",
        "Мунтха в 6-м доме: год работы над препятствиями — нагрузка, конкуренты, здоровье требуют внимания; "
        "дисциплина и режим приносят победу.",
        "Мунтха в 7-м доме: в центре партнёрство и брак; важно договариваться, избегать конфликтов и решений "
        "сгоряча.",
        "Мунтха в 8-м доме: год перемен и глубоких процессов; берегите здоровье и финансы, избегайте риска, "
        "хорошо для исследований и духовной практики.",
        "Мунтха в 9-м доме: год удачи, наставников, путешествий и веры; благоприятно для учёбы и важных решений.",
        "Мунтха в 10-м доме: год карьеры и признания; хорошее время для повышения, проектов и публичности.",
        "Мунтха в 11-м доме: год доходов, исполнения желаний и полезных связей; друзья и сообщества помогают.",
        "Мунтха в 12-м доме: год расходов, уединения и завершений; удачно для отдыха, поездок за границу и "
        "духовных практик, но следите за тратами.",
    ],
    "en": [
        "Muntha in the 1st house: a year about yourself — a fresh start, care for health and appearance, growing "
        "confidence.",
        "Muntha in the 2nd house: money, family and speech are in focus; a good year to sort out finances and save.",
        "Muntha in the 3rd house: a year of bold steps, travel, learning and communication; luck comes through your "
        "own efforts.",
        "Muntha in the 4th house: home, mother, property and inner peace are central; household chores are likely — "
        "protect your peace of mind.",
        "Muntha in the 5th house: creativity, children, study and romance; a good year for ideas and learning.",
        "Muntha in the 6th house: a year of working through obstacles — workload, rivals and health need attention; "
        "discipline and routine bring victory.",
        "Muntha in the 7th house: partnership and marriage are central; negotiate, avoid conflicts and hasty "
        "decisions.",
        "Muntha in the 8th house: a year of change and deep processes; protect health and finances, avoid risk; good "
        "for research and spiritual practice.",
        "Muntha in the 9th house: a year of luck, teachers, travel and faith; favourable for study and big decisions.",
        "Muntha in the 10th house: a year of career and recognition; a good time for promotion, projects and "
        "visibility.",
        "Muntha in the 11th house: a year of income, wishes fulfilled and useful connections; friends and "
        "communities help.",
        "Muntha in the 12th house: a year of expenses, solitude and endings; good for rest, travel abroad and "
        "spiritual practice, but watch your spending.",
    ],
}

# Знак лагны года — тон года
YEAR_LAGNA = {
    "ru": [
        "Овен: год энергии, инициативы и новых начинаний; действуйте смело, но без спешки.",
        "Телец: год стабильности, накоплений и удовольствий; хорошо укреплять материальную базу.",
        "Близнецы: год общения, учёбы, поездок и множества дел; важно не распыляться.",
        "Рак: год дома, семьи и чувств; эмоции сильнее обычного, важна забота о близких.",
        "Лев: год самовыражения, лидерства и признания; время проявить себя.",
        "Дева: год порядка, работы и здоровья; детали и систематичность приносят плоды.",
        "Весы: год партнёрства, договоров и гармонии; удачен для отношений и сотрудничества.",
        "Скорпион: год глубоких перемен и внутренней силы; возможны кризисы, ведущие к обновлению.",
        "Стрелец: год расширения, учёбы, путешествий и поиска смысла.",
        "Козерог: год труда, ответственности и долгосрочных целей; результат — за упорство.",
        "Водолей: год друзей, сообществ и нестандартных идей; удачен для новых проектов.",
        "Рыбы: год интуиции, творчества и духовности; важны отдых и вдохновение.",
    ],
    "en": [
        "Aries: a year of energy, initiative and new beginnings; act boldly but without haste.",
        "Taurus: a year of stability, savings and pleasures; good for building a material base.",
        "Gemini: a year of communication, study, trips and many tasks; avoid spreading yourself thin.",
        "Cancer: a year of home, family and feelings; emotions run stronger, care for loved ones matters.",
        "Leo: a year of self-expression, leadership and recognition; time to show yourself.",
        "Virgo: a year of order, work and health; detail and system bring results.",
        "Libra: a year of partnership, agreements and harmony; good for relationships and cooperation.",
        "Scorpio: a year of deep change and inner strength; crises may lead to renewal.",
        "Sagittarius: a year of expansion, study, travel and the search for meaning.",
        "Capricorn: a year of work, responsibility and long-term goals; persistence pays off.",
        "Aquarius: a year of friends, communities and unconventional ideas; good for new projects.",
        "Pisces: a year of intuition, creativity and spirituality; rest and inspiration matter.",
    ],
}

# Медленные планеты: что приносят дому года (кратко)
NATURE = {
    "ru": {"benefic": "поддерживает эту сферу", "malefic_good": "даёт силу и победу в этой сфере",
           "malefic": "требует в этой сфере терпения и осторожности"},
    "en": {"benefic": "supports this area", "malefic_good": "gives strength and victory in this area",
           "malefic": "calls for patience and care in this area"},
}
BENEFIC = {"Ju", "Ve", "Mo", "Me"}
UPACHAYA = {3, 6, 10, 11}


def planet_effect(lang: str, code: str, house: int) -> str:
    n = NATURE[lang]
    if code in BENEFIC:
        return n["benefic"]
    return n["malefic_good"] if house in UPACHAYA else n["malefic"]
