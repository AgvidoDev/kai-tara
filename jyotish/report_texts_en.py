"""Birth chart report texts (English). Same structure as report_texts.py."""

LAGNA = [
    "Aries rising gives an energetic, direct and brave character. You start fast, like to be first and catch fire "
    "with ideas; the lesson is to finish what you start and not jump to conclusions. Appearance: lively, a "
    "determined look, a sporty manner.",
    "Taurus rising brings calm, reliability and a taste for the good life. You build solidly and value stability, "
    "beauty and comfort; your strength is patience, your weakness stubbornness. Appearance: a pleasant voice, "
    "soft features, an unhurried pace.",
    "Gemini rising gives a lively mind, curiosity and sociability. Communication, learning, trade and switching "
    "roles come easily; the lesson is to focus on what matters. Appearance: youthful, expressive, quick-spoken.",
    "Cancer rising brings sensitivity, care and a strong bond with family and home. You read people well, create "
    "comfort and protect your own; the lesson is not to sink into hurt feelings and moods. Appearance: soft, "
    "expressive eyes, a changeable look.",
    "Leo rising gives dignity, generosity and natural leadership. You need recognition and room to shine, and you "
    "inspire others; the lesson is not to confuse confidence with pride. Appearance: good posture, a bright, "
    "noticeable presence.",
    "Virgo rising brings an analytical mind, practicality and a love of order. You see details and know how to "
    "improve things and serve a cause; the lesson is not to get stuck in criticism and worry. Appearance: neat, "
    "reserved, youthful.",
    "Libra rising gives diplomacy, a sense of proportion and beauty, and a focus on partnership. You negotiate and "
    "create harmony; the lesson is not to lose yourself trying to please everyone. Appearance: charm, balance, "
    "good taste.",
    "Scorpio rising brings depth, willpower and intuition. You go through transformations and come out stronger, "
    "and you see what is hidden; the lesson is to let go of control and grudges. Appearance: a piercing gaze, "
    "magnetism, privacy.",
    "Sagittarius rising gives optimism, faith and a search for meaning. You are drawn to knowledge, travel and "
    "teachers, generous and frank; the lesson is not to promise more than you can do. Appearance: open, "
    "broad gestures, cheerful.",
    "Capricorn rising brings discipline, responsibility and ambition. You climb slowly but surely, and success "
    "comes with the years; the lesson is to leave room for joy and rest. Appearance: serious, composed, lean.",
    "Aquarius rising gives independence, originality and an interest in people and ideas. You think your own way "
    "and value freedom and friendship; the lesson is to join ideals with practice. Appearance: unusual, friendly "
    "but detached.",
    "Pisces rising brings gentleness, imagination and spiritual sensitivity. You are compassionate and creative "
    "and feel the atmosphere around you; the lesson is to set boundaries and avoid illusions. Appearance: a "
    "dreamy look, softness, fluid movement.",
]

MOON_SIGN = [
    "Moon in Aries: emotions flare up fast and fade fast. You need freedom to act and new challenges; release "
    "irritation through movement and sport.",
    "Moon in Taurus — exalted: emotional stability, loyalty and a love of beauty and comfort. Nature, good food "
    "and stability calm you.",
    "Moon in Gemini: mind and feelings are closely linked — you need to talk things through. Conversation and new "
    "information lift your mood.",
    "Moon in Cancer — own sign: deep sensitivity, care and attachment to home and family. Protect yourself from "
    "other people's emotions.",
    "Moon in Leo: a need for recognition, warmth and attention. You give love generously and expect the same; "
    "creativity is the best outlet for your feelings.",
    "Moon in Virgo: emotions pass through analysis and you want things to be “right”. Order and useful work calm "
    "you; routine and care for your health ease anxiety.",
    "Moon in Libra: a need for harmony and partnership. Conflict throws you off balance; beauty, art and good "
    "company restore you.",
    "Moon in Scorpio — debilitated: feelings run deep and strong but are hard to let go. Practices of trust, "
    "psychological work and forgiveness help.",
    "Moon in Sagittarius: optimism and a hunger for meaning and freedom. Study, travel and inspiring ideas are the "
    "best cure for low moods.",
    "Moon in Capricorn: restraint and responsibility in feelings. You are reliable but rarely allow yourself to be "
    "vulnerable; give yourself permission to rest and receive warmth.",
    "Moon in Aquarius: emotional independence and friendliness. You need personal space and like-minded people; "
    "you make sense of feelings through ideas.",
    "Moon in Pisces: high sensitivity, compassion and a rich imagination. Creativity, music, spiritual practice "
    "and silence help.",
]

NAK_PERSON = [
    "Ashwini: speed, initiative and a gift for helping and healing; you love starting new things.",
    "Bharani: strength, responsibility and the ability to carry a heavy load; a passionate nature.",
    "Krittika: a sharp mind, directness and resolve; the ability to purify and cut away the excess.",
    "Rohini: charm, a sense of beauty, creative and material gifts.",
    "Mrigashira: curiosity, gentleness and an endless search — for knowledge, experience, meaning.",
    "Ardra: intellect, emotional depth and the ability to renew yourself through crises.",
    "Punarvasu: optimism, kindness and the ability to bounce back from any difficulty.",
    "Pushya: care, reliability and respect for tradition; one of the most auspicious nakshatras.",
    "Ashlesha: insight, strategic thinking and strong intuition.",
    "Magha: nobility, respect for lineage and tradition, a drive to lead.",
    "Purva Phalguni: love of life, creativity, the ability to enjoy and share joy.",
    "Uttara Phalguni: generosity, reliability in partnerships and agreements, a sense of duty.",
    "Hasta: skilled hands, practicality, resourcefulness and a sense of humour.",
    "Chitra: artistic taste, a love of beauty and making things, a vivid individuality.",
    "Swati: independence, flexibility, diplomacy and business sense.",
    "Vishakha: determination and persistence; you follow your goal to the end.",
    "Anuradha: friendliness, devotion and teamwork.",
    "Jyeshtha: the responsibility of the eldest, protecting the weak, inner strength.",
    "Mula: a drive to get to the root, a research mind, the ability to start from scratch.",
    "Purva Ashadha: inspiration, persuasiveness and an unbeatable spirit.",
    "Uttara Ashadha: principles, honesty and victory that comes with persistence.",
    "Shravana: the ability to listen and learn, wisdom, a bond with mentors.",
    "Dhanishtha: musicality, energy, prosperity and a wish for recognition.",
    "Shatabhisha: independent thinking, an interest in mysteries and healing.",
    "Purva Bhadrapada: passion, idealism and a strong will to transform.",
    "Uttara Bhadrapada: depth, wisdom, calm and steadiness.",
    "Revati: gentleness, compassion, care for others and fine perception.",
]

DIGNITY = {
    "exalted": "{planet} is exalted — one of the strongest positions: its themes ({karaka}) unfold easily and "
               "bring visible results.",
    "own": "{planet} is in its own sign — a confident, stable position: its themes ({karaka}) are your support.",
    "friend": "{planet} is in a friendly sign — a supportive position: its themes ({karaka}) work in your favour.",
    "neutral": "{planet} is in a neutral sign — its themes ({karaka}) show up evenly, and much depends on your "
               "effort.",
    "enemy": "{planet} is in an unfriendly sign — its themes ({karaka}) take more effort; upayas help here.",
    "debilitated": "{planet} is debilitated — a vulnerable position: its themes ({karaka}) are an area of growth "
                   "and lessons. Upayas help especially.",
}
RETRO = "The planet is retrograde: its themes act more deeply and inwardly, often returning to past experience."

PLANET_HOUSE = {
    "Su": ["self-confidence, leadership and a strong will; take care not to overshadow others",
           "income through status and ties with authority; pride in your family, a weighty word",
           "courage, initiative and success in your own projects and communication",
           "a strong bond with your father and home; a wish for influence in the family, interest in property",
           "creative talent, intelligence, pride in children; success in education and self-expression",
           "strength in work and competition, victory over rivals; protect your health from overwork",
           "a bright partner or a need for equality in relationships; take care not to dominate",
           "an interest in mysteries and transformation; change through crises, look after your health",
           "luck, faith, respect for teachers and father; a pull towards knowledge and long journeys",
           "a strong career, a drive for status and recognition; success in leadership roles",
           "income and influential friends, wishes fulfilled through connections",
           "a leaning towards solitude and spirituality, work abroad or behind the scenes"],
    "Mo": ["emotional openness, charm, changeable moods",
           "love of family and comfort, income through caring for people, a pleasant voice",
           "curiosity, frequent short trips, closeness with siblings",
           "strong attachment to home and mother, a need for emotional security",
           "a creative and emotional nature, love of children, a rich imagination",
           "worries about work and health; look after your digestion and nerves",
           "emotional dependence on your partner, a search for closeness and understanding",
           "deep emotions, intuition, interest in psychology; emotional hygiene matters",
           "optimism, faith, a love of travel and spiritual knowledge",
           "public life, work with people, a career you invest feelings in",
           "many friends, income through people and communities, wishes fulfilled",
           "sensitivity, a rich inner life, a need for solitude and rest"],
    "Ma": ["energy, courage, athleticism; learn to manage your temper",
           "decisiveness with money, sharp speech; watch your words",
           "huge courage and drive — one of the best positions for Mars",
           "energy in home and property matters; avoid conflict in the family",
           "competitiveness and a gambling streak, energetic children; be careful with speculation",
           "a strong position: victory over rivals, stamina, success at work",
           "passion in relationships; avoid arguments with your partner",
           "a taste for risk and extremes; protect your health and avoid injuries",
           "fighting for your beliefs, activity in study and travel",
           "a strong career, leadership, success in technical and active professions",
           "income through energy and initiative, active friends",
           "hidden energy, expenses; sport and spiritual practice help"],
    "Me": ["a sharp mind, wit, youthfulness, a gift for communication",
           "income through intellect, trade and words; a good memory",
           "sociability, a talent for writing and journalism, trade",
           "an intellectual atmosphere at home, a good education, interest in property",
           "a brilliant mind, talent for study and creativity, clever children",
           "analytical ability, success with paperwork and service",
           "business partnership, a talkative partner, success with contracts",
           "an interest in research, psychology and hidden knowledge",
           "a love of knowledge, philosophy, teaching and travel",
           "a career in communication, trade, consulting, IT",
           "income through connections, trade and intellectual work",
           "a rich imagination, interest in foreign languages and subtle matters"],
    "Ju": ["wisdom, optimism, respect from others; a fortunate position for life as a whole",
           "prosperity, a good family, wise speech; money comes through knowledge",
           "wisdom in communication, support from loved ones; growth through your own efforts",
           "happiness at home, a good education, family well-being",
           "one of the best positions: intelligence, luck with children, creativity and learning",
           "success in work and service; watch your diet and weight",
           "a wise and reliable partner, a happy marriage and business alliances",
           "longevity, interest in spiritual knowledge, luck with inheritance and joint finances",
           "one of the best positions: luck, mentors, faith, higher education",
           "a respected career, success in education, law, consulting",
           "large income, influential friends, wishes fulfilled",
           "spirituality, generosity, charity; spending on good causes"],
    "Ve": ["charm, attractiveness, artistic taste",
           "prosperity, graceful speech, a love of good food and beautiful things",
           "creativity in communication, artistry, pleasant short trips",
           "a beautiful home, comfort, good vehicles",
           "romance, creative talents, a love of art",
           "difficulties in love from high expectations; success in beauty and service",
           "a harmonious marriage, an attractive partner, happy alliances",
           "sensuality, income through a partner or inheritance",
           "a love of travel and art, luck through foreigners",
           "a career in art, beauty, design, finance",
           "income through beauty and connections, pleasant friends",
           "enjoying comfort and privacy, spending on pleasures; a good position for spiritual love"],
    "Sa": ["seriousness, responsibility, a slow but sure path to success",
           "money comes through work and over time; restraint in speech and family",
           "persistence and willpower, success through long effort",
           "responsibility for home and parents; home can be a source of pressure",
           "a serious approach to study and creativity; children may come later",
           "a strong position: endurance, overcoming difficulties, success at work",
           "a late or mature marriage, a reliable but demanding partner",
           "longevity, interest in deep knowledge; look after your health",
           "a serious attitude to faith and teachers, learning through experience",
           "a career built through hard work; status comes with age",
           "one of the best positions: steady income and reliable connections over the years",
           "a leaning towards solitude, work in closed institutions or abroad"],
    "Ra": ["a strong urge to stand out, an unconventional image; a risk of self-deception",
           "a hunger for wealth, unusual sources of income; be careful with words",
           "courage, success in media and technology — a strong position for Rahu",
           "restlessness at home, frequent moves or foreign influence",
           "unusual talents, an interest in speculation — be careful with risk",
           "a strong position: victory over rivals, success in struggle and work",
           "an unusual partner, a foreigner or someone from another background",
           "an interest in mysteries and the occult, sudden changes",
           "unconventional beliefs, an interest in other cultures",
           "ambition, fast career growth, work with technology or abroad",
           "large income, especially through networks and technology — a strong position",
           "ties with foreign lands, expenses, interest in the spiritual and hidden"],
    "Ke": ["intuition, detachment, spiritual searching",
           "an unusual attitude to money and family, reserved speech",
           "courage and intuitive decisions, distance from siblings",
           "a feeling of not quite belonging at home, a pull towards spiritual grounding",
           "an intuitive mind, interest in spiritual knowledge; a special relationship with children",
           "victory over enemies and illness through inner strength",
           "karmic relationships; take care not to withdraw",
           "strong intuition, interest in the occult and psychology",
           "your own spiritual path, doubts about other people's truths",
           "an unconventional career, indifference to status",
           "income comes unexpectedly, a small circle of friends",
           "one of the best positions for spiritual liberation and meditation"],
}

HOUSE_LORD = ("The lord of the {h} house ({lord}) sits in the {w} house — the themes “{th}” are linked to "
              "“{tw}”.")

YOGA = {
    "gaja_kesari": ("Gaja Kesari yoga", "Jupiter in a kendra from the Moon: wisdom, respect from others, the "
                    "ability to get out of difficulties and help others."),
    "budha_aditya": ("Budha Aditya yoga", "Sun and Mercury together: a sharp mind, eloquence, success in study "
                     "and intellectual work."),
    "chandra_mangala": ("Chandra Mangala yoga", "Moon and Mars together: business sense and a knack for earning, "
                        "but also a quick temper."),
    "ruchaka": ("Ruchaka yoga (Mahapurusha)", "A strong Mars in a kendra: courage, leadership, success in active "
                "and technical fields."),
    "bhadra": ("Bhadra yoga (Mahapurusha)", "A strong Mercury in a kendra: intellect, eloquence, business talent."),
    "hamsa": ("Hamsa yoga (Mahapurusha)", "A strong Jupiter in a kendra: wisdom, nobility, respect and luck."),
    "malavya": ("Malavya yoga (Mahapurusha)", "A strong Venus in a kendra: charm, taste, comfort and harmony in "
                "relationships."),
    "sasha": ("Sasha yoga (Mahapurusha)", "A strong Saturn in a kendra: endurance, organising talent, authority "
              "that comes with age."),
    "raja": ("Raja yoga", "Lords of a kendra and a trikona ({planets}) together: potential for status, recognition "
             "and success, especially in their dashas."),
    "dhana": ("Dhana yoga", "Lords of the houses of money and fortune ({planets}) together: potential for "
              "prosperity and financial growth."),
    "vipareeta": ("Vipareeta Raja yoga", "The lord of the {house} house in the {in} house: success that comes "
                  "through overcoming difficulties and crises."),
    "mangal_dosha": ("Mangal dosha", "Mars in the {house} house: passion and drive in relationships. It is "
                     "considered in compatibility; it softens if the partner has the same dosha, and with "
                     "maturity in the relationship."),
    "kemadruma": ("Kemadruma yoga", "No planets beside the Moon: periods of loneliness and emotional "
                  "instability. Spiritual practice, support from loved ones and the Moon's upayas help."),
}

DASHA_LORD = {
    "Su": "a time to show yourself and strengthen your status and health; relations with bosses and father matter",
    "Mo": "a period of emotions, family and home; moods change, care for yourself and loved ones matters",
    "Ma": "a period of energy, action and struggle; good for sport, property and bold steps",
    "Ra": "a period of ambition, change and unexpected chances; don't fall for illusions",
    "Ju": "a period of growth, learning, luck and mentors; a good time for family and children",
    "Sa": "a period of work, responsibility and maturing; results come slowly but surely",
    "Me": "a period of learning, communication, trade and business; paperwork and contracts matter",
    "Ke": "a period of inner searching and letting go of the unnecessary; good for spiritual practice",
    "Ve": "a period of love, comfort, creativity and prosperity; good for marriage and beauty",
}

SECTION = {
    "title": "Birth chart reading", "for": "Prepared by Kai Tara", "lagna": "Lagna — your character",
    "moon": "Moon — your inner world", "planets": "Planets in your chart", "houses": "Areas of life (houses)",
    "yogas": "Yogas — special combinations", "no_yogas": "No pronounced classical yogas were found — that is "
    "neither good nor bad: the chart unfolds through the planets and dashas.", "dashas": "Life periods (dashas)",
    "upaya": "Upayas — recommendations", "about": "About the calculation", "current": "now",
    "antar": "Current antardasha",
    "no_time": "No birth time was given: the Lagna is unknown, houses are counted from the Moon, and the Moon's "
    "position is for noon. Add your birth time for an accurate reading.",
    "method": "Sidereal zodiac, Lahiri ayanamsha, whole-sign houses, Vimshottari dasha. This report is for "
    "information only and is not a substitute for professional advice. Birth data is not stored.",
    "in_house": "in the {h} house", "dasha_line": "{lord}: {start} – {end}", "dasha_in_chart":
    "In your chart {planet} sits in the {h} house ({theme}) — these themes come to the fore.",
    "stones": "Gemstones are chosen only from a full chart in a consultation.",
}
