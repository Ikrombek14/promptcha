"""Tayyor promptning determinal (LLM'siz) tekshiruvi.

Ball LLM tomonidan qoʻyiladi — u adashishi mumkin. Bu yerdagilar esa matnning oʻzidan
koʻrinadigan, bahssiz nuqsonlar. Ikki joyda ishlatiladi:
  1. `pipeline.generate` — nuqson topilsa prompt bir marta avtomatik qayta yoziladi;
  2. `evals/` — har oʻzgarishdan keyin 20 ta haqiqiy soʻrovda oʻlchash.

Nega kerak boʻldi: «restoran uchun menyu» soʻroviga yozilgan promptda menyu sarlavhasi
"Biznes nomi" deb qolib ketgan (vosita uni haqiqiy nom deb chizadi) va bitta boʻlim
ikki marta takrorlangan edi — ball esa 82 edi.
"""

from __future__ import annotations

import re

#: Joʻrik oʻrniga qolib ketishi mumkin boʻlgan «yolgʻon qiymat» soʻzlari (uz/ru/en)
FAKE_VALUE_WORDS: frozenset[str] = frozenset(
    {
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
)

PLACEHOLDER_RE = re.compile(r"\[([^\]\n]{1,60})\]")
#: Qoʻshtirnoq ichidagi matn — menyu boʻlimi, sarlavha, logotip yozuvi shu koʻrinishda keladi
QUOTED_RE = re.compile(r"[\"“]([^\"”\n]{1,60})[\"”]")

#: Bir faktga ikki xil joʻrik ishlatilmasin
TOKEN_GROUPS: tuple[tuple[frozenset[str], str], ...] = (
    (frozenset({"NARX", "PRICE", "ЦЕНА"}), "narx"),
    (frozenset({"TELEFON", "PHONE", "ТЕЛЕФОН"}), "telefon"),
    (frozenset({"MANZIL", "ADDRESS", "АДРЕС"}), "manzil"),
)


def fake_values(prompt: str) -> list[str]:
    """Qavssiz, haqiqiy qiymatdek koʻringan joʻriklar: `"Biznes nomi"`."""
    out = []
    for q in QUOTED_RE.findall(prompt):
        text = q.strip()
        if text.startswith("[") and text.endswith("]"):
            continue
        if text.strip("[]").lower() in FAKE_VALUE_WORDS:
            out.append(text)
    return out


def bad_placeholders(prompt: str) -> list[str]:
    """Qavs ichida, lekin notoʻgʻri shaklda: kichik harfli yoki jumlaga oʻxshagan."""
    out = []
    for p in PLACEHOLDER_RE.findall(prompt):
        inner = p.strip()
        if len(inner.split()) > 4 or inner != inner.upper():
            out.append(inner)
    return out


def duplicates(prompt: str) -> list[str]:
    """Takrorlangan boʻlim nomi yoki uzun qator."""
    out: list[str] = []

    seen: dict[str, int] = {}
    original: dict[str, str] = {}
    for q in QUOTED_RE.findall(prompt):
        text = q.strip()
        key = text.lower()
        if len(key) >= 3:
            seen[key] = seen.get(key, 0) + 1
            original.setdefault(key, text)
    out += [f'takroriy boʻlim: "{original[k]}" ×{v}' for k, v in seen.items() if v > 1]

    lines: dict[str, int] = {}
    for raw in prompt.splitlines():
        line = raw.strip().strip("-•*").strip().lower()
        if len(line) >= 25:
            lines[line] = lines.get(line, 0) + 1
    out += [f"takroriy qator ×{v}: {k[:40]}…" for k, v in lines.items() if v > 1]
    return out


def inconsistent_tokens(prompt: str) -> list[str]:
    """Bir faktga ikki xil joʻrik: `[NARX]` va `[PRICE]` bitta promptda."""
    tokens = {p.strip().upper() for p in PLACEHOLDER_RE.findall(prompt)}
    out = []
    for group, label in TOKEN_GROUPS:
        hit = tokens & group
        if len(hit) > 1:
            out.append(f"{label}: {', '.join(sorted(hit))}")
    return out


def defects(prompt: str) -> list[str]:
    """Topilgan nuqsonlar roʻyxati (boʻsh boʻlsa — prompt toza).

    Faqat **bahssiz** narsalar: joʻrik oʻrnidagi oddiy soʻz, takror, notoʻgʻri joʻrik shakli.
    Uslub va mazmun baholash — review'ning ishi.
    """
    out: list[str] = []
    for value in fake_values(prompt):
        out.append(
            f'"{value}" — joʻrik oʻrniga oddiy soʻz qolgan; [KATTA HARF, QAVSDA] koʻrinishida yozing'
        )
    for bad in bad_placeholders(prompt):
        out.append(f"[{bad}] — joʻrik qisqa va KATTA HARFDA boʻlishi kerak")
    out += duplicates(prompt)
    out += inconsistent_tokens(prompt)
    return out


# --------------------------------------------------------------------------- avtomatik tuzatish


def _fix_fake_values(prompt: str) -> str:
    """`"Biznes nomi"` → `"[BIZNES NOMI]"` — vosita uni haqiqiy nom deb chizmasin."""

    def sub(m: re.Match[str]) -> str:
        inner = m.group(1).strip()
        if inner.lower() in FAKE_VALUE_WORDS:
            return '"[' + inner.upper() + ']"'
        return m.group(0)

    return QUOTED_RE.sub(sub, prompt)


def _fix_placeholder_case(prompt: str) -> str:
    """`[narx]` → `[NARX]`. Jumlaga oʻxshagan uzun joʻrik tegilmaydi — uni model tuzatadi."""

    def sub(m: re.Match[str]) -> str:
        inner = m.group(1).strip()
        if len(inner.split()) <= 4 and inner != inner.upper():
            return "[" + inner.upper() + "]"
        return m.group(0)

    return PLACEHOLDER_RE.sub(sub, prompt)


def _fix_token_groups(prompt: str) -> str:
    """Bir faktga ikki token boʻlsa, birinchi uchraganiga keltiriladi."""
    for group, _label in TOKEN_GROUPS:
        found = [
            p.strip().upper()
            for p in PLACEHOLDER_RE.findall(prompt)
            if p.strip().upper() in group
        ]
        if len(set(found)) > 1:
            keep = found[0]
            for other in set(found) - {keep}:
                prompt = re.sub(
                    re.escape("[" + other + "]"),
                    "[" + keep + "]",
                    prompt,
                    flags=re.IGNORECASE,
                )
    return prompt


def _drop_repeated_lines(prompt: str) -> str:
    """Bir xil uzun qator ikki marta boʻlsa — ikkinchisi olib tashlanadi."""
    seen: set[str] = set()
    out = []
    for line in prompt.splitlines():
        key = line.strip().lower()
        if len(key) >= 25:
            if key in seen:
                continue
            seen.add(key)
        out.append(line)
    return chr(10).join(out)


def repair(prompt: str) -> tuple[str, list[str]]:
    """Mexanik tuzatib boʻladiganini tuzatadi; qolgan nuqsonlarni qaytaradi.

    Qaytgan roʻyxat boʻsh boʻlmasa — modeldan qayta yozish soʻraladi (`pipeline`).
    Takrorlangan boʻlim nomi shunday holat: qaysi birini olib tashlashni faqat model biladi.
    """
    fixed = _drop_repeated_lines(
        _fix_token_groups(_fix_placeholder_case(_fix_fake_values(prompt)))
    )
    return fixed, defects(fixed)
