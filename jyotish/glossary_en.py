"""English glossary: same keys as jyotish/glossary.py (deep links are language-neutral)."""
from __future__ import annotations

import re

from .kb import NAKSHATRA, RASHI
from .texts import HOUSE, KARAKA, NAKSHATRA_DEITY_EN, NAKSHATRA_NAME, NATURE, PLANET, SIGN, SIGN_SKT_LATIN, ordinal_en


def build(Term) -> dict:
    T: dict = {}

    def add(t):
        T[t.key] = t

    I = "(?i)"
    for t in [
        Term("jyotish", "Jyotish",
             "Vedic (Indian) astrology. The word means “the science of light”. It measures planets against the "
             "real constellations and focuses on the Moon, the nakshatras and life periods (dashas).",
             "Jyotish is one of the six auxiliary disciplines of the Vedas. It differs from Western astrology in "
             "three ways: 1) the sidereal zodiac — signs are tied to the stars, not to the spring equinox; "
             "2) the Moon matters more than the Sun — in India “your sign” is your Moon sign; 3) the dasha "
             "system shows which planet “runs” your life in particular years.",
             [I + r"jyotish\w*|vedic astrology"], ["sidereal", "nakshatra", "dasha"]),
        Term("sidereal", "Sidereal zodiac",
             "A zodiac tied to the actual stars. Today it is about 24° behind the familiar (tropical) zodiac, "
             "so your Vedic sign is often one sign “earlier” than your Western sign.",
             "Western astrology starts Aries at the spring equinox. Because of the precession of the Earth's "
             "axis, that point drifts against the stars by 1° every ~72 years; the gap is now about 24° "
             "(the ayanamsha). So if you are Aries by Western dates, your Sun is most likely in sidereal Pisces. "
             "The bot can still forecast by your familiar sign: it blends the two sidereal signs in proportion "
             "to your dates.",
             [I + r"sidereal\w*"], ["ayanamsha", "rashi", "jyotish"]),
        Term("ayanamsha", "Ayanamsha",
             "The offset between the Western and Vedic zodiacs (about 24° today). We use the Lahiri ayanamsha, "
             "the official one in India.",
             "There are several schools (Lahiri, Raman, Krishnamurti) that differ by 1–2°. Lahiri is used by the "
             "Indian government for its almanacs (panchangas), so most Vedic astrologers use it. The ayanamsha "
             "decides signs and nakshatras, especially when a planet sits near a boundary.",
             [I + r"ayanamsha\w*"], ["sidereal"]),
        Term("rashi", "Rashi",
             "A zodiac sign in Sanskrit. Jyotish has the same 12 signs, Aries to Pisces, but counted by the stars.",
             "A rashi is a 30° slice of the sky: Mesha (Aries), Vrishabha (Taurus), Mithuna (Gemini), Karka "
             "(Cancer), Simha (Leo), Kanya (Virgo), Tula (Libra), Vrishchika (Scorpio), Dhanu (Sagittarius), "
             "Makara (Capricorn), Kumbha (Aquarius), Meena (Pisces). Each sign has a ruling planet.",
             [I + r"\brashi\b"], ["sidereal", "nakshatra"]),
        Term("nakshatra", "Nakshatra",
             "A lunar mansion — one of 27 sectors of the sky, 13°20′ each. The Moon spends about a day in each. "
             "Your birth Moon's nakshatra is considered your key trait in Jyotish.",
             "If a sign is a “district”, a nakshatra is a “street”. The 27 nakshatras are finer than the 12 signs "
             "and describe character and destiny more precisely. Each has a ruling planet (which starts the "
             "dasha sequence), a deity and a nature (soft, sharp, fixed, etc.) used to choose good days. Each "
             "nakshatra has 4 padas (quarters).",
             [I + r"nakshatra\w*"], ["pada", "tarabala", "dasha", "muhurta"]),
        Term("pada", "Pada",
             "A quarter of a nakshatra (3°20′). It refines the nakshatra's character; there are 108 padas in all.",
             "Each of the 27 nakshatras has 4 padas. A pada links the nakshatra to the navamsha, an important "
             "divisional chart for marriage and inner strength.",
             [I + r"\bpadas?\b"], ["nakshatra"]),
        Term("lagna", "Lagna (Ascendant)",
             "The sign rising in the east at the moment of birth. It sets the starting point for the houses. "
             "It needs an exact birth time.",
             "The lagna changes roughly every 2 hours, so it cannot be known without a birth time. The 12 houses "
             "are counted from it: the 1st is you, the 7th your partner, the 10th your career, and so on. "
             "Jyotish uses whole-sign houses: the lagna sign is the 1st house, the next sign the 2nd.",
             [I + r"lagna\w*|ascendant\w*"], ["house", "rashi"]),
        Term("house", "House (bhava)",
             "An area of life in the chart: money, family, work, partnership and so on. There are 12. "
             "“In the 7th house” means the event touches that area.",
             "Houses are counted from a reference point: from the lagna in a personal chart, from your sign "
             "(Moon or Sun) in general forecasts. If you are Libra, Scorpio is your 2nd house (money) and Aries "
             "your 7th (partnership). A transiting planet brings its themes into that house.",
             [I + r"\bhouses?\b"], ["lagna", "gochara"]),
        Term("gochara", "Gochara (transits)",
             "The current movement of planets relative to your sign. By classical rules each planet is "
             "favourable only in certain houses from the Moon.",
             "For example, Jupiter is good in the 2nd, 5th, 7th, 9th and 11th houses from the Moon, Saturn in the "
             "3rd, 6th and 11th. The rules come from the classic Phaladeepika. Slow planets (Saturn, Jupiter, "
             "Rahu/Ketu) set the background for months and years, fast ones for days and weeks. A good transit "
             "can be blocked by another planet — that's called vedha.",
             [I + r"gochara|transit\w*"], ["vedha", "house", "sade_sati"]),
        Term("vedha", "Vedha",
             "An “obstruction”: a favourable transit is blocked when another planet stands in a specific "
             "opposing house, and the promised support weakens.",
             "Each planet has a paired vedha house for every good house. For instance, Jupiter in the 5th from "
             "the Moon is blocked by a planet in the 4th. “Father and son” pairs — Sun and Saturn, Moon and "
             "Mercury — don't block each other.",
             [I + r"vedha\w*|obstruction"], ["gochara"]),
        Term("upaya", "Upayas",
             "Vedic remedies to balance planetary influences: mantras, charity, fasting, colours, weekdays. "
             "Gemstones only after consulting an astrologer.",
             "Upayas don't “cancel” karma; they help you get through a hard period more gently and strengthen "
             "supportive influences. The safest and most universal are charity and mantras on the planet's day. "
             "Gemstones amplify a planet strongly, so they are chosen only from the full chart.",
             [I + r"\bupayas?\b|remed(?:y|ies)"], ["dasha", "tapas"]),
        Term("tapas", "Tapas",
             "Discipline and voluntary restraint for a long-term goal. Literally “heat”. Not self-torture but "
             "consistency: a small practice every day without a break.",
             "In the Vedic tradition tapas builds the power of intention. It works on the body (daily routine, "
             "purity, non-violence), speech (truthful and kind words) and mind (calm, restraint). Tapas grows "
             "from consistency — say, early rising or meditation for 40 days in a row — and is quickly lost "
             "to outbursts of anger and boasting. It is especially helpful during Sade Sati and a nodal shift.",
             [I + r"\btapas\b|disciplin\w*"], ["upaya", "sade_sati"]),
    ]:
        add(t)

    for t in [
        Term("dasha", "Dasha",
             "A life period “ruled” by one planet. The Vimshottari system splits 120 years into 9 periods of "
             "6 to 20 years and shows which themes dominate those years.",
             "The order: Ketu 7 years, Venus 20, Sun 6, Moon 10, Mars 7, Rahu 18, Jupiter 16, Saturn 19, "
             "Mercury 17. Which dasha your life starts with depends on your birth Moon's nakshatra. A major period "
             "(mahadasha) is divided into sub-periods (antardashas) of the same 9 planets.",
             [I + r"\bdashas?\b|vimshottari"], ["mahadasha", "antardasha", "nakshatra"], "periods"),
        Term("mahadasha", "Mahadasha",
             "A planet's major period (6–20 years). It sets the main storyline of those years: that planet's "
             "themes and the houses it rules in your chart.",
             "A change of mahadasha often feels like a new life chapter: a move, a new job, marriage, a crisis or "
             "a rise. The outcome depends on the planet's strength in the birth chart and the house it occupies.",
             [I + r"mahadasha\w*"], ["dasha", "antardasha"], "periods"),
        Term("antardasha", "Antardasha",
             "A sub-period inside a mahadasha (a few months to 3 years). It shows which theme is in the "
             "foreground right now.",
             "For example, Saturn antardasha in a Jupiter mahadasha mixes growth with responsibility. An even "
             "finer level is the pratyantar dasha (weeks to months).",
             [I + r"antardasha\w*"], ["dasha", "mahadasha"], "periods"),
        Term("sade_sati", "Sade Sati",
             "A 7.5-year period when Saturn crosses the sign before your Moon, the Moon's sign and the sign after "
             "it. A time of responsibility, fatigue and restructuring — and of maturing.",
             "Three phases of ~2.5 years: the first brings expenses and worry, the second (peak) pressure on "
             "health and emotions, the third financial and family matters and gradual relief. Everyone goes "
             "through Sade Sati 2–3 times in life. No need to fear it: Saturn rewards honest work and "
             "discipline. Saturn's upayas on Saturdays help.",
             [I + r"sade[- ]?sati"], ["ashtama_shani", "kantaka_shani", "upaya"], "periods"),
        Term("ashtama_shani", "Ashtama Shani",
             "Saturn in the 8th house from the Moon (~2.5 years): obstacles, delays, health and other people's "
             "money.",
             "One of Saturn's hardest transits. Avoid risks and big debts, watch your health, and use the time "
             "for deep inner work.",
             [I + r"ashtama[- ]?shani"], ["sade_sati", "kantaka_shani"], "periods"),
        Term("kantaka_shani", "Kantaka Shani",
             "Saturn in the 4th house from the Moon (~2.5 years): pressure at home and in the family, property "
             "issues, a lack of peace.",
             "“Kantaka” means thorn. The period asks for patience in family matters; moves and renovations run "
             "late.",
             [I + r"kantaka[- ]?shani"], ["sade_sati", "ashtama_shani"], "periods"),
        Term("retro", "Retrograde",
             "A planet's apparent backward motion as seen from Earth. A time to review and return to old matters; "
             "postpone new starts in that planet's area.",
             "Retrograde Mercury — mix-ups with paperwork and communication; Venus — revisiting relationships and "
             "purchases; Mars — energy turns inward. In Jyotish a retrograde planet is strong but acts unusually. "
             "Rahu and Ketu are always retrograde — that's normal for them.",
             [I + r"retrograd\w*|\(R\)"], ["station"], "periods"),
        Term("station", "Planetary station",
             "The moment a planet “stops” and changes direction (direct ↔ retrograde). Its influence is "
             "especially strong around those days.",
             "Station days are turning points in the planet's themes. Make important decisions in that area "
             "after the planet goes direct again.",
             [I + r"station\w*|\bdirect\b"], ["retro"], "periods"),
        Term("ingress", "Ingress",
             "A planet entering a new sign. For slow planets (Jupiter, Saturn, Rahu/Ketu) it changes the "
             "background for months or years.",
             "In a forecast it's written as “Jupiter → Leo”. After the ingress the planet occupies a different "
             "house from your sign, and so a different area of life.",
             [I + r"ingress\w*"], ["gochara"], "periods"),
        Term("eclipse", "Eclipse",
             "Solar (at New Moon) or lunar (at Full Moon). In Jyotish eclipses are linked to Rahu and Ketu and are "
             "times of sharp turns; important beginnings aren't planned on eclipse days.",
             "Eclipses come in “seasons” every six months. They hit hardest when they fall on your Moon sign, "
             "lagna or Sun.",
             [I + r"eclipse\w*"], ["rahu", "ketu"], "periods"),
    ]:
        add(t)

    for t in [
        Term("new_moon", "New Moon (Amavasya)",
             "The conjunction of the Sun and Moon. The start of the lunar month: a time for intentions and new "
             "beginnings. The New Moon's sign shows the theme of the month.",
             "In a lunation forecast we look at which house from your sign the New Moon falls in — that's the "
             "“focus of the month”. The Amavasya day itself is considered weak for important matters; start "
             "1–3 days later.",
             [I + r"new moon|amavasya"], ["full_moon", "tithi"], "moon"),
        Term("full_moon", "Full Moon (Purnima)",
             "The opposition of the Sun and Moon. The peak of the lunar cycle: emotions run high and results "
             "become visible.",
             "Purnima is good for spiritual practice and charity. In relationships and work the Full Moon "
             "reveals what has been ripening all month.",
             [I + r"full moon|purnima"], ["new_moon", "tithi"], "moon"),
        Term("lunation", "Lunation",
             "A New Moon or Full Moon — the key points of the lunar month. A lunation forecast lasts until the "
             "next event of the same kind.",
             "", [I + r"lunation\w*"], ["new_moon", "full_moon"], "moon"),
        Term("tithi", "Tithi",
             "A lunar day: the time it takes the Moon to move 12° further from the Sun. A month has 30 tithis; "
             "their quality is used to time activities.",
             "Tithis fall into 5 groups: Nanda (joy) — 1, 6, 11; Bhadra (goodness) — 2, 7, 12; Jaya (victory) — "
             "3, 8, 13; Rikta (empty) — 4, 9, 14; Purna (full) — 5, 10, 15. Rikta tithis are unfavourable for "
             "beginnings. Shukla paksha is the waxing Moon, Krishna paksha the waning Moon.",
             [I + r"tithis?"], ["ekadashi", "new_moon", "muhurta"], "moon"),
        Term("ekadashi", "Ekadashi",
             "The 11th lunar day (twice a month). A traditional day of fasting and spiritual practice — a "
             "cleansing day for body and mind.",
             "On Ekadashi people abstain from grains and beans. Fasting on this day is believed to soften the "
             "influence of the Moon and Saturn.",
             [I + r"ekadashi"], ["tithi"], "moon"),
        Term("tarabala", "Tara Bala",
             "The strength of a day by nakshatra: counted from your birth Moon's nakshatra to the current Moon's "
             "nakshatra. 9 kinds of days, from “wealth” to “danger”.",
             "The taras: 1 Janma (birth, neutral), 2 Sampat (wealth, good), 3 Vipat (danger, bad), 4 Kshema "
             "(well-being, good), 5 Pratyak (obstacles, bad), 6 Sadhana (achievement, excellent), 7 Naidhana "
             "(destruction, bad), 8 Mitra (friend, good), 9 Parama Mitra (best friend, excellent). It needs your "
             "birth Moon's nakshatra.",
             [I + r"tara[- ]?bala"], ["chandrabala", "nakshatra"], "moon"),
        Term("chandrabala", "Chandra Bala",
             "The Moon's strength for you today: which house from your birth Moon the transiting Moon is in. "
             "The 1st, 3rd, 6th, 7th, 10th and 11th are favourable.",
             "Chandra Bala changes every ~2.5 days. Together with Tara Bala it is the basis of personal timing "
             "(muhurta).",
             [I + r"chandra[- ]?bala"], ["tarabala", "muhurta"], "moon"),
        Term("muhurta", "Muhurta",
             "Choosing an auspicious time for an undertaking: a wedding, a move, a deal, a trip. It weighs the "
             "nakshatra, tithi, weekday and your personal factors.",
             "A full muhurta is calculated to the minute. Our calendar gives a simplified day-level version — "
             "enough for everyday matters.",
             [I + r"muhurta\w*"], ["tarabala", "chandrabala", "tithi"], "moon"),
        Term("ashtakuta", "Ashta Kuta",
             "The classical compatibility system based on two people's Moons: 8 criteria, up to 36 points. "
             "18 or more is considered acceptable.",
             "The kutas: Varna (1) — spiritual values, Vashya (2) — mutual influence, Tara (3) — destiny and "
             "health, Yoni (4) — physical compatibility, Graha Maitri (5) — friendship of the sign lords, "
             "psychology, Gana (6) — temperament, Bhakoot (7) — family and prosperity, Nadi (8) — health and "
             "offspring. Nadi dosha (0 of 8) and Bhakoot dosha are considered serious, but have exceptions.",
             [I + r"ashta[- ]?kuta|kuta[- ]?milan\w*|guna milan\w*"], ["nakshatra"], "moon"),
        Term("vara", "Vara (weekday)",
             "In Jyotish each weekday is ruled by a planet: Sun — Sunday, Moon — Monday, Mars — Tuesday, "
             "Mercury — Wednesday, Jupiter — Thursday, Venus — Friday, Saturn — Saturday.",
             "Plan activities on the right planet's day: study and beginnings on Thursday, beauty purchases and "
             "dates on Friday, disputes and sport on Tuesday.",
             [I + r"\bvara\b"], ["muhurta"], "moon"),
    ]:
        add(t)

    planet_long = {
        "Su": "The Sun is the soul, father, authority, health and vitality. A strong Sun gives confidence and "
              "leadership; a weak one, issues with self-esteem and bosses.",
        "Mo": "The Moon is the mind, emotions, mother and mood. In Jyotish the Moon matters more than the Sun: "
              "its sign and nakshatra describe your inner world, and transits and dashas are counted from it.",
        "Ma": "Mars is energy, courage, disputes, sport, property and siblings. It gives the power to act; under "
              "stress — conflicts, injuries, haste.",
        "Me": "Mercury is speech, intellect, trade, paperwork and learning. It governs negotiations and deals.",
        "Ju": "Jupiter (Guru) is growth, wisdom, teachers, children and luck. The most benefic planet: where it "
              "goes, things expand. It spends about a year in each sign.",
        "Ve": "Venus (Shukra) is love, marriage, beauty, comfort, art and money for pleasures.",
        "Sa": "Saturn (Shani) is time, discipline, work, limits and long-term results. It spends ~2.5 years in a "
              "sign, so its transits are life's main “backgrounds”.",
        "Ra": "Rahu is the north lunar node, a shadow planet: ambition, hunger for the new, foreign things, "
              "technology, illusions and sudden chances. Always retrograde.",
        "Ke": "Ketu is the south lunar node, a shadow planet: detachment, spirituality, intuition, losses and "
              "release from the unnecessary. Always opposite Rahu.",
    }
    planet_key = {"Su": "sun", "Mo": "moon", "Ma": "mars", "Me": "mercury", "Ju": "jupiter", "Ve": "venus",
                  "Sa": "saturn", "Ra": "rahu", "Ke": "ketu"}
    planet_pat = {"Su": r"\bSun\b", "Mo": r"\bMoon(?!'s nakshatra)\b", "Ma": r"\bMars\b", "Me": r"\bMercury\b",
                  "Ju": r"\bJupiter\b", "Ve": r"\bVenus\b", "Sa": r"\bSaturn\b", "Ra": r"\bRahu\b",
                  "Ke": r"\bKetu\b"}
    for c, key in planet_key.items():
        add(Term(key, PLANET["en"][c], f"{PLANET['en'][c]}: {KARAKA['en'][c]}.", planet_long[c],
                 [planet_pat[c]], ["gochara", "dasha"], "planets"))

    sign_key = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius",
                "capricorn", "aquarius", "pisces"]
    sign_nature = [
        "fire, movable: initiative, courage, beginnings", "earth, fixed: stability, resources, taste",
        "air, dual: communication, curiosity", "water, movable: care, home, emotions",
        "fire, fixed: dignity, leadership, creativity", "earth, dual: analysis, service, order",
        "air, movable: partnership, balance, trade", "water, fixed: depth, secrets, transformation",
        "fire, dual: faith, teaching, long journeys", "earth, movable: work, career, structure",
        "air, fixed: ideas, communities, science", "water, dual: compassion, spirituality, dreams",
    ]
    for i, key in enumerate(sign_key):
        add(Term(key, f"{SIGN['en'][i]} ({SIGN_SKT_LATIN[i]})",
                 f"{SIGN['en'][i]} — {sign_nature[i]}. Ruler — {PLANET['en'][RASHI[i]['lord']]}.",
                 f"In Jyotish signs are counted by the stars (sidereally), so sidereal {SIGN['en'][i]} falls about "
                 "24 days later than the Western one. A “sidereal” sign in a forecast is the Vedic sign.",
                 [rf"\b{SIGN['en'][i]}\b"], ["rashi", "sidereal"], "signs"))

    house_long = {
        1: "Body, health, character, how others see you. Transits here feel personal.",
        2: "Savings, earned income, family, speech, food. Key for money forecasts.",
        3: "Courage, your own efforts, short trips, communication, neighbours, siblings.",
        4: "Home, mother, property, vehicles, education, inner peace.",
        5: "Children, creativity, romance, study, intellect, speculation, past merit.",
        6: "Daily work, service, health and illness, debts, enemies and rivals.",
        7: "Marriage, partnership, contracts, clients, public relations.",
        8: "Crises and transformation, inheritance, other people's money, taxes, insurance, secrets.",
        9: "Luck, faith, teachers, father, long journeys, higher education.",
        10: "Career, status, profession, leadership, reputation.",
        11: "Income and gains, wishes fulfilled, friends, patrons, communities.",
        12: "Expenses, losses, solitude, sleep, foreign lands, hospitals, spiritual liberation.",
    }
    for h in range(1, 13):
        o = ordinal_en(h)
        add(Term(f"house_{h}", f"{o} house", f"{o} house: {HOUSE['en'][h]}.", house_long[h],
                 [rf"(?i)(?<!\d){o}\s+house\b"], ["house", "gochara"], "houses"))

    meaning = [
        "swift starts, healing, help", "creative power and responsibility, trials",
        "sharpness, purification by fire, resolve", "growth, beauty, fertility, material prosperity",
        "seeking, curiosity, gentleness", "storm, change, cleansing through crisis",
        "return, renewal, optimism", "nourishment, care — the most auspicious nakshatra",
        "insight, cunning, serpent wisdom", "lineage, ancestors, power and tradition",
        "pleasure, rest, creativity, love", "alliances, agreements, generosity",
        "craftsmanship, skill of the hands, dexterity", "beauty, design, architecture, brilliance",
        "independence, flexibility, trade", "determination, reaching the goal",
        "friendship, devotion, cooperation", "seniority, protection, responsibility",
        "the root, getting to the core, breaking the old", "invincibility, inspiration, purification by water",
        "final victory, principles", "listening, learning, connection",
        "wealth, music, fame", "healing, mysteries, a hundred physicians",
        "passion, austerity, fire of transformation", "depth, wisdom, stability",
        "care on the journey, completion, prosperity",
    ]
    nature_hint = {
        "лёгкая/быстрая": "good for trade, travel, healing and study",
        "постоянная": "good for lasting matters: building, buying a home, weddings",
        "мягкая": "good for love, art, buying clothes and jewellery, friendship",
        "острая": "suits decisive action, surgery, cutting harmful ties; not for beginnings",
        "жестокая": "suits struggle and overcoming; unfavourable for peaceful beginnings",
        "подвижная": "good for travel, moving, buying vehicles, change",
        "смешанная": "suits routine and current affairs",
    }
    from .glossary import NAK_KEY
    for i, key in enumerate(NAK_KEY):
        n = NAKSHATRA[i]
        name = NAKSHATRA_NAME["en"][i]
        span0 = i * 360 / 27
        r0, r1 = SIGN["en"][int(span0 // 30)], SIGN["en"][int((span0 + 13.33) // 30) % 12]
        where = r0 if r0 == r1 else f"{r0} / {r1}"
        lord = PLANET["en"][n["lord"]]
        pat = re.escape(name).replace(r"\ ", r"[- ]")
        add(Term(key, f"{name} nakshatra",
                 f"{name} ({ordinal_en(i + 1)} nakshatra, {where}): {meaning[i]}. Ruler — {lord}, deity — "
                 f"{NAKSHATRA_DEITY_EN[i]}.",
                 f"Its nature is {NATURE['en'][n['nature']]}: {nature_hint[n['nature']]}. If this is your Moon's "
                 f"nakshatra, your life began in the {lord} dasha, and “{meaning[i]}” is part of your character. "
                 "When the Moon passes through it (every ~27 days), its themes grow stronger for everyone.",
                 [rf"\b{pat}\b"], ["nakshatra", "tarabala"], "nakshatras"))
    return T


CATEGORIES_EN = {
    "basics": "Basics", "periods": "Periods and transits", "moon": "Moon and calendar", "planets": "Planets",
    "signs": "Signs", "houses": "Houses", "nakshatras": "Nakshatras",
}
