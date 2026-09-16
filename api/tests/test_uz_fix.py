from app.ai.pipeline import uz_fix


def test_uz_fix_replaces_wrong_apostrophes_after_o_and_g():
    assert uz_fix("Rasm qanday uslubda bo‘lsin? yog’och, ko'k, g`oya") == (
        "Rasm qanday uslubda boʻlsin? yogʻoch, koʻk, gʻoya"
    )


def test_uz_fix_replaces_turkish_dotless_i():
    assert uz_fix("kısa, orta, İlova") == "kisa, orta, Ilova"


def test_uz_fix_keeps_correct_and_unrelated_apostrophes():
    assert uz_fix("oʻzbek sunʼiy ta'kid it's") == "oʻzbek sunʼiy ta'kid it's"


def test_uz_fix_leaves_closing_quotes_after_o_or_g():
    """Izohlardagi ‘…’ qoʻshtirnoq soʻz oxirida (guessing’) — bu apostrof emas."""
    assert (
        uz_fix("‘ask before guessing’ qoidasi, ‘logo’ soʻzi")
        == "‘ask before guessing’ qoidasi, ‘logo’ soʻzi"
    )
