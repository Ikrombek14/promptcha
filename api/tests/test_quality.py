"""Determinal sifat tekshiruvi — `ai/quality.py`.

Namunalar egasi topgan haqiqiy nuqsondan olingan: menyu promptida "Biznes nomi"
joʻrik oʻrniga oddiy soʻz boʻlib qolgan va "Ichimliklar" boʻlimi ikki marta yozilgan.
"""

from app.ai import quality

MENU_BAD = (
    'An A4 portrait restaurant menu for "Biznes nomi". Sections with headings '
    '"Salatlar", "Birinchi taomlar", "Ichimliklar", "Ichimliklar"; each item lists '
    'name, description and price "[narx] soʻm" right-aligned.'
)

MENU_GOOD = (
    'An A4 portrait restaurant menu for "[RESTORAN NOMI]". Sections: "Salatlar", '
    '"Birinchi taomlar", "Ichimliklar"; each item lists name, description and price '
    'in the format "[NARX] soʻm", right-aligned with dotted leaders.'
)


def test_clean_prompt_has_no_defects():
    assert quality.defects(MENU_GOOD) == []


def test_bare_label_is_caught():
    found = " ".join(quality.defects(MENU_BAD))
    assert "Biznes nomi" in found


def test_duplicate_section_is_caught():
    found = " ".join(quality.defects(MENU_BAD))
    assert "Ichimliklar" in found and "×2" in found


def test_lowercase_placeholder_is_caught():
    assert any("narx" in d for d in quality.defects(MENU_BAD))


def test_sentence_in_brackets_is_not_a_placeholder():
    text = "Use [a short friendly line about the new dish] at the top."
    assert quality.defects(text)


def test_two_tokens_for_one_fact():
    text = "Price shown as [NARX] in the list and [PRICE] in the footer."
    assert any("narx" in d for d in quality.defects(text))


def test_real_name_in_quotes_is_not_a_defect():
    """Foydalanuvchi bergan nom — joʻrik emas, tegilmaydi."""
    assert quality.defects('A logo for "Navroʻz" cafe, warm colours.') == []


def test_repeated_long_line_is_caught():
    line = "Every dish shows the name, a short description and the price on the right."
    assert quality.defects(f"{line}\n{line}")
