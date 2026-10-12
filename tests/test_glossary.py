import re

from bot.glossary import card, linkify, terms_keyboard
from jyotish.glossary import NAK_KEY, TERMS, find_terms, matches


def test_all_keys_are_deeplink_safe():
    for k in TERMS:
        assert re.fullmatch(r"[A-Za-z0-9_]{1,60}", "g_" + k), k


def test_related_terms_exist():
    for t in TERMS.values():
        for r in t.related:
            assert r in TERMS, (t.key, r)


def test_every_term_has_pattern_and_short_text():
    for t in TERMS.values():
        assert t.patterns and t.short, t.key


def test_specific_house_beats_generic():
    assert find_terms("Фокус месяца — 8-й дом, кризисы") == ["house_8"]
    assert find_terms("в 11-м доме: доходы") == ["house_11"]


def test_first_occurrence_only():
    ms = matches("Сатурн в 4-м. Сатурн снова.")
    assert [k for *_, k in ms] == ["saturn"]


def test_finds_core_terms():
    txt = ("Знак лунации: Весы, накшатра Вишакха. Саде-Сати, вторая фаза. Меркурий ретроградный. "
           "Махадаша Раху, антардаша Юпитера. Тара-бала: Сампат.")
    keys = set(find_terms(txt))
    assert {"libra", "nakshatra", "vishakha", "sade_sati", "mercury", "retro", "mahadasha",
            "rahu", "antardasha", "jupiter", "tarabala"} <= keys


def test_nakshatra_keys_cover_27():
    assert len(NAK_KEY) == 27 and all(k in TERMS for k in NAK_KEY)


def test_linkify_wraps_outside_tags_only():
    html = '<b>Весы</b> — накшатра <a href="x">Вишакха</a>, Сатурн'
    out = linkify(html, "testbot")
    assert '<b><a href="https://t.me/testbot?start=g_libra">Весы</a></b>' in out
    assert '<a href="x">Вишакха</a>' in out            # внутри чужой ссылки не трогаем
    assert "g_vishakha" not in out
    assert 'start=g_saturn">Сатурн</a>' in out
    assert re.sub(r"<[^>]+>", "", out) == re.sub(r"<[^>]+>", "", html)  # видимый текст не меняется


def test_linkify_does_not_touch_attributes_or_entities():
    html = 'Дом &amp; <i title="Сатурн">семья</i>'
    out = linkify(html, "b")
    assert 'title="Сатурн"' in out and "&amp;" in out


def test_linkify_without_username_is_noop():
    assert linkify("Сатурн", None) == "Сатурн"


def test_card_and_keyboard():
    text, kb = card("sade_sati")
    assert "Саде-Сати" in text
    datas = [b.callback_data for row in kb.inline_keyboard for b in row]
    assert "glm:sade_sati" in datas and "gl:ashtama_shani" in datas
    text_full, kb_full = card("sade_sati", full=True)
    assert len(text_full) > len(text)
    assert "glm:sade_sati" not in [b.callback_data for row in kb_full.inline_keyboard for b in row]


def test_terms_keyboard_limits_and_callback_size():
    kb = terms_keyboard(list(TERMS)[:40])
    buttons = [b for row in kb.inline_keyboard for b in row]
    assert len(buttons) <= 24
    assert all(len(b.callback_data.encode()) <= 64 for b in buttons)
