"""Promptning determinal (LLM'siz) sifat tekshiruvlari.

Nega kerak: ball LLM tomonidan qoʻyiladi — u adashishi mumkin. Quyidagilar esa matnning
oʻzidan koʻrinadigan, bahssiz nuqsonlar. Bitta ham oʻtmasligi kerak:

1. Joʻrik oʻrniga oddiy soʻz — menyuda "Biznes nomi" deb yozilsa, Canva shuni chizadi.
2. Takror — bitta boʻlim yoki qator ikki marta.
3. Joʻrik shakli — hammasi [KATTA HARF, QAVSDA] va bir fakt bitta token.
4. Foydalanuvchi bergan fakt yoʻqolmagan.
5. Uzunlik playbook chegarasida.
"""

from __future__ import annotations

import re

#: Joʻrik oʻrniga ishlatilishi mumkin boʻlgan «yolgʻon qiymat» soʻzlari (uz/ru/en)
FAKE_VALUE_WORDS = {
    "biznes nomi",
    "brend nomi",
    "restoran nomi",
    "kompaniya nomi",
    "nomi",
    "narx",
    "narxi",
    "telefon",
    "manzil",
    "название бизнеса",
    "название",
    "цена",
    "телефон",
    "адрес",
    "business name",
    "brand name",
    "company name",
    "your brand",
    "your business",
    "brand",
    "company",
    "name",
    "price",
    "phone",
    "address",
}

PLACEHOLDER_RE = re.compile(r"\[([^\]\n]{1,60})\]")
#: Qoʻshtirnoq ichidagi matn — menyu boʻlimi, sarlavha, logotip yozuvi shu koʻrinishda keladi
QUOTED_RE = re.compile(r"[\"“]([^\"”\n]{1,60})[\"”]")


def fake_values(prompt: str) -> list[str]:
    """Qavssiz, haqiqiy qiymatdek koʻringan joʻriklar ("Biznes nomi")."""
    bad = []
    for q in QUOTED_RE.findall(prompt):
        inner = q.strip().strip("[]").lower()
        if inner in FAKE_VALUE_WORDS and not (q.strip().startswith("[") and q.strip().endswith("]")):
            bad.append(q.strip())
    return bad


def bad_placeholders(prompt: str) -> list[str]:
    """Qavs ichida boʻlsa ham notoʻgʻri shakldagilar: kichik harfli yoki jumlaga oʻxshagan."""
    bad = []
    for p in PLACEHOLDER_RE.findall(prompt):
        inner = p.strip()
        if len(inner.split()) > 4:  # jumla — joʻrik emas
            bad.append(inner)
        elif inner != inner.upper():  # [narx] — katta harf boʻlishi kerak
            bad.append(inner)
    return bad


def duplicates(prompt: str) -> list[str]:
    """Takrorlangan boʻlim nomi yoki qator (qisqa, maʼnosiz takrorlar hisobga olinmaydi)."""
    out: list[str] = []

    seen: dict[str, int] = {}
    for q in QUOTED_RE.findall(prompt):
        key = q.strip().lower()
        if len(key) < 3:
            continue
        seen[key] = seen.get(key, 0) + 1
    out += [f'"{k}" ×{v}' for k, v in seen.items() if v > 1]

    lines: dict[str, int] = {}
    for raw in prompt.splitlines():
        line = raw.strip().strip("-•*").strip()
        if len(line) < 25:
            continue
        lines[line.lower()] = lines.get(line.lower(), 0) + 1
    out += [f"qator ×{v}: {k[:40]}…" for k, v in lines.items() if v > 1]
    return out


def inconsistent_tokens(prompt: str) -> list[str]:
    """Bir faktga ikki xil joʻrik: [NARX] va [PRICE] bir promptda."""
    tokens = {p.strip().upper() for p in PLACEHOLDER_RE.findall(prompt)}
    pairs = [
        ({"NARX", "PRICE", "ЦЕНА"}, "narx"),
        ({"TELEFON", "PHONE", "ТЕЛЕФОН"}, "telefon"),
        ({"MANZIL", "ADDRESS", "АДРЕС"}, "manzil"),
    ]
    out = []
    for group, label in pairs:
        hit = tokens & group
        if len(hit) > 1:
            out.append(f"{label}: {', '.join(sorted(hit))}")
    return out


def length_bounds(kind: str) -> tuple[int, int]:
    return (50, 170) if kind in ("image", "video") else (120, 420)


def run_checks(prompt: str, kind: str, must_contain: list[str]) -> dict:
    """Barcha tekshiruv. `ok` — hammasi oʻtgan boʻlsa."""
    words = len(prompt.split())
    lo, hi = length_bounds(kind)
    missing = [m for m in must_contain if m.lower() not in prompt.lower()]
    problems = {
        "fake_values": fake_values(prompt),
        "bad_placeholders": bad_placeholders(prompt),
        "duplicates": duplicates(prompt),
        "inconsistent_tokens": inconsistent_tokens(prompt),
        "missing_facts": missing,
        "length": [] if lo <= words <= hi else [f"{words} soʻz ({lo}–{hi} kutilgan)"],
    }
    return {"ok": not any(problems.values()), "problems": {k: v for k, v in problems.items() if v}}
