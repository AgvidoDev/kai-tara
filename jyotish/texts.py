"""Тексты расчётного ядра на разных языках.

Расчёт отдаёт структуру (планета, дом, код флага), текст собирается здесь. Новый язык —
это ещё один словарь в каждой таблице (ключи языков: "ru", "en").
"""
from __future__ import annotations

from .kb import HOUSE_THEMES, NAKSHATRA, PLANET_KARAKA, PLANET_RU, RASHI, REMEDIES, TITHI_RU

LANGS = ("ru", "en")
DEFAULT_LANG = "ru"

# ------------------------------------------------------------------ знаки, планеты
SIGN = {
    "ru": [r["ru"] for r in RASHI],
    "en": ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
           "Sagittarius", "Capricorn", "Aquarius", "Pisces"],
}
SIGN_SKT = [r["skt"] for r in RASHI]
SIGN_SKT_LATIN = ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya", "Tula", "Vrishchika",
                  "Dhanu", "Makara", "Kumbha", "Meena"]

PLANET = {
    "ru": dict(PLANET_RU),
    "en": {"Su": "Sun", "Mo": "Moon", "Ma": "Mars", "Me": "Mercury", "Ju": "Jupiter", "Ve": "Venus",
           "Sa": "Saturn", "Ra": "Rahu", "Ke": "Ketu"},
}
KARAKA = {
    "ru": dict(PLANET_KARAKA),
    "en": {"Su": "authority, father, vitality", "Mo": "emotions, mother, mood",
           "Ma": "energy, conflicts, property", "Me": "communication, trade, paperwork",
           "Ju": "growth, luck, mentors, children", "Ve": "love, comfort, money, beauty",
           "Sa": "discipline, limits, hard work", "Ra": "ambition, illusions, sudden chances",
           "Ke": "detachment, spirituality, losses"},
}
HOUSE = {
    "ru": dict(HOUSE_THEMES),
    "en": {1: "self, health, appearance", 2: "money, family, speech, food",
           3: "initiative, courage, short trips, siblings", 4: "home, mother, property, inner peace",
           5: "children, creativity, romance, learning", 6: "work, health, rivals, debts",
           7: "partnership, marriage, contracts", 8: "crises, transformation, other people's money",
           9: "luck, teachers, long journeys, faith", 10: "career, status, leadership",
           11: "income, wishes fulfilled, friends", 12: "expenses, solitude, abroad, sleep"},
}

NAKSHATRA_NAME = {
    "ru": [n["ru"] for n in NAKSHATRA],
    "en": ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya",
           "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
           "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
           "Dhanishtha", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"],
}
NAKSHATRA_DEITY_EN = ["the Ashvins", "Yama", "Agni", "Brahma", "Soma", "Rudra", "Aditi", "Brihaspati",
                      "the Nagas", "the Pitris", "Bhaga", "Aryaman", "Savitar", "Tvashtar", "Vayu",
                      "Indra-Agni", "Mitra", "Indra", "Nirriti", "Apas", "the Vishvadevas", "Vishnu",
                      "the Vasus", "Varuna", "Aja Ekapada", "Ahirbudhnya", "Pushan"]
NATURE_KEYS = ["лёгкая/быстрая", "постоянная", "мягкая", "острая", "жестокая", "подвижная", "смешанная"]
NATURE = {
    "ru": {k: k for k in NATURE_KEYS},
    "en": {"лёгкая/быстрая": "light/swift", "постоянная": "fixed", "мягкая": "soft", "острая": "sharp",
           "жестокая": "fierce", "подвижная": "movable", "смешанная": "mixed"},
}
NATURE_DO = {
    "ru": {"лёгкая/быстрая": "торговля, поездки, лечение, обучение, быстрые дела",
           "постоянная": "фундаментальные дела: покупка жилья, долгосрочные договоры, посадки",
           "мягкая": "свидания, искусство, покупка одежды и украшений, дружеские встречи",
           "острая": "решительные действия, разрыв вредных связей, медицинские процедуры",
           "жестокая": "борьба с препятствиями, сложные переговоры; мирные начинания лучше отложить",
           "подвижная": "поездки, переезды, покупка транспорта, перемены",
           "смешанная": "текущие и рутинные дела"},
    "en": {"лёгкая/быстрая": "trade, travel, healing, study, quick tasks",
           "постоянная": "lasting matters: buying a home, long-term contracts, planting",
           "мягкая": "dates, art, buying clothes and jewellery, meeting friends",
           "острая": "decisive action, cutting harmful ties, medical procedures",
           "жестокая": "tackling obstacles, tough negotiations; postpone peaceful beginnings",
           "подвижная": "travel, moving house, buying a vehicle, change",
           "смешанная": "routine and everyday matters"},
}

# ------------------------------------------------------------------ лунации и тон
LUNATION_ADVICE = {
    "ru": {1: "время перезапуска: начните личный проект, займитесь собой и здоровьем",
           2: "наведите порядок в финансах и семейных делах, следите за словами",
           3: "проявляйте инициативу, хорошо для коротких поездок, учёбы, переговоров",
           4: "фокус на доме: ремонт, переезд, отношения с родителями",
           5: "творчество, дети, романтика; удачный месяц для обучения",
           6: "разгребайте рабочие завалы и долги, займитесь здоровьем",
           7: "главная тема — партнёрство: договоры, брак, деловые союзы",
           8: "не рискуйте деньгами, хорошее время для глубокой внутренней работы",
           9: "расширяйте горизонты: дальние поездки, наставники, учёба",
           10: "карьерный рывок: заявите о себе, берите ответственность",
           11: "время пожинать плоды: доходы, нетворкинг, исполнение планов",
           12: "сбавьте темп, отдыхайте, завершайте старое; осторожно с расходами"},
    "en": {1: "time for a reset: start a personal project, focus on yourself and your health",
           2: "put your finances and family matters in order, mind your words",
           3: "take the initiative; good for short trips, study and negotiations",
           4: "focus on home: renovation, moving, relations with parents",
           5: "creativity, children, romance; a good month for learning",
           6: "clear the backlog at work and pay off debts, look after your health",
           7: "the main theme is partnership: contracts, marriage, business alliances",
           8: "don't gamble with money; a good time for deep inner work",
           9: "broaden your horizons: long journeys, mentors, study",
           10: "a career push: make yourself known and take responsibility",
           11: "time to reap the rewards: income, networking, plans coming true",
           12: "slow down, rest and wrap up old business; be careful with spending"},
}
TONE = {
    "ru": {"good": "благоприятный", "bad": "напряжённый", "mixed": "смешанный", "calm": "спокойный"},
    "en": {"good": "favourable", "bad": "challenging", "mixed": "mixed", "calm": "calm"},
}


# ------------------------------------------------------------------ транзиты
def transit_note(lang: str, planet: str, house: int) -> str:
    if lang == "en":
        return f"{PLANET['en'][planet]} ({KARAKA['en'][planet]}) in the {ordinal_en(house)} house: {HOUSE['en'][house]}"
    return f"{PLANET['ru'][planet]} ({KARAKA['ru'][planet]}) в {house}-м доме: {HOUSE['ru'][house]}"


SADE_STAGE = {"ru": {12: "первая", 1: "вторая, пиковая", 2: "третья, завершающая"},
              "en": {12: "first", 1: "second, peak", 2: "third, final"}}


def flag_text(lang: str, flag: dict) -> str:
    code = flag["code"]
    en = lang == "en"
    if code == "sade_sati":
        st = SADE_STAGE[lang][flag["house"]]
        txt = f"Sade Sati, {st} phase" if en else f"Саде-Сати, {st} фаза"
    elif code == "ashtama_shani":
        txt = "Ashtama Shani (Saturn in the 8th)" if en else "Аштама-Шани (Сатурн в 8-м)"
    elif code == "kantaka_shani":
        txt = "Kantaka Shani (Saturn in the 4th)" if en else "Кантака-Шани (Сатурн в 4-м)"
    elif code == "jupiter_support":
        h = flag["house"]
        txt = f"Jupiter supports you ({ordinal_en(h)} house)" if en else f"Юпитер поддерживает ({h}-й дом)"
    else:
        txt = code
    if flag.get("mix_rashi") is not None:
        txt = f"{mix_prefix(lang, flag['mix_rashi'], flag['mix_weight'])}: {txt}"
    return txt


def mix_prefix(lang: str, rashi: int, weight: float) -> str:
    w = round(weight * 100)
    return f"{SIGN['en'][rashi]} sid. ({w}%)" if lang == "en" else f"{SIGN['ru'][rashi]} сид. ({w}%)"


def factor_text(lang: str, f: dict) -> str:
    note = transit_note(lang, f["planet"], f["house"])
    if f.get("mix_rashi") is not None:
        w = round(f["mix_weight"] * 100)
        tag = f"{SIGN['en'][f['mix_rashi']]} sid., {w}%" if lang == "en" else f"{SIGN['ru'][f['mix_rashi']]} сид., {w}%"
        note = f"[{tag}] {note}"
    return note


# ------------------------------------------------------------------ события
ECLIPSE_TYPE = {
    "ru": {"total": "полное", "annular": "кольцеобразное", "hybrid": "гибридное", "partial": "частное",
           "penumbral": "полутеневое"},
    "en": {"total": "total", "annular": "annular", "hybrid": "hybrid", "partial": "partial",
           "penumbral": "penumbral"},
}


def event_text(lang: str, e: dict) -> str:
    k, en = e["kind"], lang == "en"
    p = PLANET[lang].get(e.get("planet") or "", "")
    sign = SIGN[lang][e["rashi"]] if e.get("rashi") is not None else ""
    if k == "ingress":
        return f"{p} → {sign}"
    if k in ("station_r", "station_d"):
        if en:
            return f"{p} turns {'retrograde' if k == 'station_r' else 'direct'} in {sign}"
        return f"{p} {'ретроградный' if k == 'station_r' else 'директный'} в знаке {sign}"
    if k == "full_moon":
        return f"Full Moon in {sign}" if en else f"Полнолуние в знаке {sign}"
    if k == "new_moon":
        return f"New Moon in {sign}" if en else f"Новолуние в знаке {sign}"
    if k == "solar_eclipse":
        t = ECLIPSE_TYPE[lang][e.get("subtype", "partial")]
        return f"Solar eclipse ({t})" if en else f"Солнечное затмение ({t})"
    if k == "lunar_eclipse":
        t = ECLIPSE_TYPE[lang][e.get("subtype", "partial")]
        return f"Lunar eclipse ({t})" if en else f"Лунное затмение ({t})"
    return k


# ------------------------------------------------------------------ панчанга
TITHI_NAME_EN = ["Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", "Saptami",
                 "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi"]


def tithi_name(lang: str, tithi: int) -> str:
    if tithi == 15:
        return "Purnima" if lang == "en" else "Пурнима"
    if tithi == 30:
        return "Amavasya" if lang == "en" else "Амавасья"
    return (TITHI_NAME_EN if lang == "en" else TITHI_RU)[(tithi - 1) % 15]


PAKSHA = {"ru": ("Шукла", "Кришна"), "en": ("Shukla", "Krishna")}
PAKSHA_LONG = {"ru": ("Шукла (растущая Луна)", "Кришна (убывающая Луна)"),
               "en": ("Shukla (waxing Moon)", "Krishna (waning Moon)")}
TITHI_GROUP = {"ru": ["Нанда", "Бхадра", "Джая", "Рикта", "Пурна"],
               "en": ["Nanda", "Bhadra", "Jaya", "Rikta", "Purna"]}
TITHI_GROUP_MEANING = {"ru": ["радость", "благо", "победа", "пустота", "полнота"],
                       "en": ["joy", "goodness", "victory", "emptiness", "fullness"]}
VARA = {"ru": ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"],
        "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}
WEEKDAY_SHORT = {"ru": ["пн", "вт", "ср", "чт", "пт", "сб", "вс"],
                 "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]}
VARA_GOOD_FOR = {
    "ru": {"Su": "дела с начальством, здоровье, госорганы", "Mo": "семья, дом, забота о себе, поездки",
           "Ma": "спорт, решительные шаги, ремонт, споры", "Me": "учёба, переговоры, документы, торговля",
           "Ju": "начинания, обучение, советы наставников, финансы", "Ve": "любовь, красота, покупки, искусство",
           "Sa": "рутина, завершение дел, уборка, дисциплина"},
    "en": {"Su": "dealing with bosses and officials, health", "Mo": "family, home, self-care, trips",
           "Ma": "sport, bold moves, repairs, disputes", "Me": "study, negotiations, paperwork, trade",
           "Ju": "new beginnings, learning, advice from mentors, finance",
           "Ve": "love, beauty, shopping, art", "Sa": "routine, finishing tasks, cleaning, discipline"},
}
TARA = {
    "ru": [("Джанма", "рождение"), ("Сампат", "богатство"), ("Випат", "опасность"), ("Кшема", "благополучие"),
           ("Пратьяк", "препятствия"), ("Садхана", "достижение"), ("Наидхана", "разрушение"),
           ("Митра", "друг"), ("Парама-митра", "лучший друг")],
    "en": [("Janma", "birth"), ("Sampat", "wealth"), ("Vipat", "danger"), ("Kshema", "well-being"),
           ("Pratyak", "obstacles"), ("Sadhana", "achievement"), ("Naidhana", "destruction"),
           ("Mitra", "friend"), ("Parama Mitra", "best friend")],
}
SPECIAL = {
    "ru": {"ekadashi": "Экадаши — день поста и очищения",
           "amavasya": "Амавасья (новолуние) — важные дела не начинают",
           "purnima": "Пурнима (полнолуние) — эмоции на пике, хорошо для духовных практик",
           "pushya": "Пушья — одна из самых благоприятных накшатр для начинаний"},
    "en": {"ekadashi": "Ekadashi — a day for fasting and cleansing",
           "amavasya": "Amavasya (New Moon) — avoid starting important things",
           "purnima": "Purnima (Full Moon) — emotions peak; good for spiritual practice",
           "pushya": "Pushya — one of the most auspicious nakshatras for beginnings"},
}

# ------------------------------------------------------------------ календарь
CAL_CATEGORY = {
    "ru": {"money": "💰 Деньги и сделки", "start": "🚀 Новые начинания", "travel": "✈️ Поездки",
           "beauty": "💇 Стрижка и красота", "health": "🩺 Начало лечения",
           "love": "💞 Свидания и отношения", "home": "🏠 Дом, переезд, покупка жилья"},
    "en": {"money": "💰 Money and deals", "start": "🚀 New beginnings", "travel": "✈️ Travel",
           "beauty": "💇 Haircut and beauty", "health": "🩺 Starting treatment",
           "love": "💞 Dates and relationships", "home": "🏠 Home, moving, buying property"},
}

# ------------------------------------------------------------------ совместимость
KUTA_NAME = {
    "ru": {"varna": "Варна", "vashya": "Вашья", "tara": "Тара", "yoni": "Йони", "maitri": "Граха-майтри",
           "gana": "Гана", "bhakoot": "Бхакут", "nadi": "Нади"},
    "en": {"varna": "Varna", "vashya": "Vashya", "tara": "Tara", "yoni": "Yoni", "maitri": "Graha Maitri",
           "gana": "Gana", "bhakoot": "Bhakoot", "nadi": "Nadi"},
}
KUTA_MEANING = {
    "ru": {"varna": "духовные ценности", "vashya": "взаимное влияние", "tara": "судьба и благополучие пары",
           "yoni": "физическая гармония", "maitri": "психологическая близость", "gana": "темперамент",
           "bhakoot": "семья и достаток", "nadi": "здоровье и потомство"},
    "en": {"varna": "spiritual values", "vashya": "mutual influence", "tara": "destiny and well-being",
           "yoni": "physical harmony", "maitri": "psychological closeness", "gana": "temperament",
           "bhakoot": "family and prosperity", "nadi": "health and offspring"},
}
VARNA_NAME = {"ru": {4: "брахман", 3: "кшатрий", 2: "вайшья", 1: "шудра"},
              "en": {4: "Brahmin", 3: "Kshatriya", 2: "Vaishya", 1: "Shudra"}}
VASHYA_NAME = {"ru": ["четвероногие", "человек", "водные", "дикие", "насекомые"],
               "en": ["quadruped", "human", "water", "wild", "insect"]}
ANIMAL = {"ru": ["лошадь", "слон", "баран", "змея", "собака", "кошка", "крыса", "корова", "буйвол",
                 "тигр", "олень", "обезьяна", "мангуст", "лев"],
          "en": ["horse", "elephant", "ram", "serpent", "dog", "cat", "rat", "cow", "buffalo",
                 "tiger", "deer", "monkey", "mongoose", "lion"]}
GANA_NAME = {"ru": ["дэва (божественная)", "манушья (человеческая)", "ракшаса (демоническая)"],
             "en": ["Deva (divine)", "Manushya (human)", "Rakshasa (demonic)"]}
NADI_NAME = {"ru": ["Ади (вата)", "Мадхья (питта)", "Антья (капха)"],
             "en": ["Adi (vata)", "Madhya (pitta)", "Antya (kapha)"]}
VERDICT = {
    "ru": {"weak": "слабая совместимость — союз потребует много работы над отношениями",
           "medium": "средняя совместимость — союз допустим, есть зоны для притирки",
           "good": "хорошая совместимость", "excellent": "отличная совместимость"},
    "en": {"weak": "low compatibility — the union will need a lot of work",
           "medium": "average compatibility — acceptable, with areas to work on",
           "good": "good compatibility", "excellent": "excellent compatibility"},
}


def kuta_detail(lang: str, k: dict) -> str:
    c, a = k["code"], k.get("args", {})
    if c == "varna":
        d = f"{VARNA_NAME[lang][a['a']]} / {VARNA_NAME[lang][a['b']]}"
    elif c == "vashya":
        d = f"{VASHYA_NAME[lang][a['a']]} / {VASHYA_NAME[lang][a['b']]}"
    elif c == "yoni":
        d = f"{ANIMAL[lang][a['a']]} / {ANIMAL[lang][a['b']]}"
    elif c == "maitri":
        d = f"{PLANET[lang][a['a']]} / {PLANET[lang][a['b']]}"
    elif c == "gana":
        d = f"{GANA_NAME[lang][a['a']]} / {GANA_NAME[lang][a['b']]}"
    elif c == "bhakoot":
        d = (f"signs {a['d1']}/{a['d2']} apart" if lang == "en" else f"знаки {a['d1']}/{a['d2']} друг от друга")
    elif c == "nadi":
        d = f"{NADI_NAME[lang][a['a']]} / {NADI_NAME[lang][a['b']]}"
    else:
        return KUTA_MEANING[lang][c]
    return f"{d} — {KUTA_MEANING[lang][c]}"


def dosha_text(lang: str, d: dict) -> str:
    en = lang == "en"
    if d["code"] == "bhakoot":
        txt = (f"Bhakoot dosha (signs {d['lo']}/{d['hi']} apart)" if en
               else f"Бхакут-доша (знаки в соотношении {d['lo']}/{d['hi']})")
        if d["cancelled"]:
            txt += " — softened: the sign lords are friends" if en else " — смягчается: управители знаков дружественны"
        return txt
    txt = "Nadi dosha (same Nadi)" if en else "Нади-доша (одинаковая нади)"
    if d["cancelled"]:
        txt += (" — softened: same sign or nakshatra but different padas" if en
                else " — смягчается: одна Луна в общем знаке или накшатре, но разные пады")
    return txt


# ------------------------------------------------------------------ упаи
REMEDIES_EN = {
    "Su": {"day": "Sunday", "mantra": "Om Suryaya Namaha", "color": "orange, gold",
           "charity": "wheat, copper, helping your father and elders",
           "practice": "rise before dawn, Surya Namaskar, offer water to the rising Sun", "stone": "ruby"},
    "Mo": {"day": "Monday", "mantra": "Om Chandraya Namaha", "color": "white, silver",
           "charity": "rice, milk, water; caring for your mother",
           "practice": "regular sleep, walks by water, meditation", "stone": "pearl"},
    "Ma": {"day": "Tuesday", "mantra": "Om Mangalaya Namaha", "color": "red",
           "charity": "red lentils, blood donation", "practice": "sport, physical work, controlling anger",
           "stone": "red coral"},
    "Me": {"day": "Wednesday", "mantra": "Om Budhaya Namaha", "color": "green",
           "charity": "green vegetables, books and study materials",
           "practice": "learning, keeping notes, honesty in speech", "stone": "emerald"},
    "Ju": {"day": "Thursday", "mantra": "Om Gurave Namaha", "color": "yellow",
           "charity": "yellow foods, turmeric; supporting teachers and education",
           "practice": "respect for mentors, studying spiritual texts", "stone": "yellow sapphire"},
    "Ve": {"day": "Friday", "mantra": "Om Shukraya Namaha", "color": "white, pastels",
           "charity": "sweets, white clothes, helping women",
           "practice": "art, beauty at home, harmony in relationships", "stone": "diamond or white sapphire"},
    "Sa": {"day": "Saturday", "mantra": "Om Shanaishcharaya Namaha", "color": "dark blue, black",
           "charity": "sesame seeds, dark clothes, helping the elderly and those in need",
           "practice": "discipline, honest work, service; fasting on Saturdays", "stone": "blue sapphire"},
    "Ra": {"day": "Saturday", "mantra": "Om Rahave Namaha", "color": "smoky grey",
           "charity": "helping the homeless, feeding stray dogs",
           "practice": "digital detox, avoiding dubious schemes, meditation", "stone": "hessonite"},
    "Ke": {"day": "Tuesday", "mantra": "Om Ketave Namaha", "color": "grey, brown",
           "charity": "blankets, helping the sick", "practice": "spiritual practice, solitude, meditation",
           "stone": "cat's eye"},
}
REMEDY = {"ru": REMEDIES, "en": REMEDIES_EN}


# ------------------------------------------------------------------ формат
def ordinal_en(n: int) -> str:
    suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def house_label(lang: str, h: int) -> str:
    return f"{ordinal_en(h)} house" if lang == "en" else f"{h}-й дом"


MONTH_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def fmt_date(d, lang: str = "ru", year: bool = True) -> str:
    """ru: 11.10.2026 / 11.10; en: 11 Oct 2026 / 11 Oct."""
    if lang == "en":
        return f"{d.day} {MONTH_EN[d.month - 1]}" + (f" {d.year}" if year else "")
    return f"{d:%d.%m.%Y}" if year else f"{d:%d.%m}"


def fmt_dt(d, lang: str = "ru") -> str:
    return f"{fmt_date(d, lang)} {d:%H:%M}"


def norm(lang: str | None) -> str:
    return lang if lang in LANGS else DEFAULT_LANG
