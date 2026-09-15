"""Model ʻ (U+02BB) kabi harflarni `\\u02bb` kod sifatida yozib yuborsa — ikkala qatlamda tiklanadi."""

from pydantic import BaseModel

from app.ai.llm import _parse_json
from app.ai.pipeline import _localize, unescape_unicode, uz_fix


class _Q(BaseModel):
    question: str


def test_parse_json_recovers_double_escaped_unicode():
    raw = '{"question": "Kimga mo\\\\u02bbljallangan?"}'  # JSON ichida ikki backslash
    assert _parse_json(_Q, raw).question == "Kimga moʻljallangan?"


def test_parse_json_keeps_normal_escapes():
    assert _parse_json(_Q, '{"question": "ko\\u02bbk \\n yangi"}').question == "koʻk \n yangi"


def test_unescape_unicode_in_plain_text():
    assert unescape_unicode("mo\\u02bbljallangan, ko\\u2019k") == "moʻljallangan, ko’k"
    assert unescape_unicode("oddiy matn \\n") == "oddiy matn \\n"


def test_uz_fix_decodes_then_normalizes():
    assert uz_fix("ko\\u2019k g\\u2018oya") == "koʻk gʻoya"


def test_localize_decodes_for_every_locale():
    assert _localize("\\u0451лка", "ru") == "ёлка"
    assert _localize("na\\u00efve", "en") == "naïve"
