from app.ai.pipeline import uz_fix


def test_uz_fix_replaces_wrong_apostrophes_after_o_and_g():
    assert uz_fix("Rasm qanday uslubda bo‘lsin? yog’och, ko'k, g`oya") == (
        "Rasm qanday uslubda boʻlsin? yogʻoch, koʻk, gʻoya"
    )


def test_uz_fix_keeps_correct_and_unrelated_apostrophes():
    assert uz_fix("oʻzbek sunʼiy ta'kid it's") == "oʻzbek sunʼiy ta'kid it's"
