"""system_prompts/*.md va examples/*/ fayllarini oʻqish. Kod oʻzgarmaydi — fayllar yaxshilanadi.

Prompt uslubi: vosita uchun maxsus fayl boʻlsa (`system_prompts/<tool>.md`, masalan midjourney,
claude) — oʻsha; boʻlmasa oila fayli (`system_prompts/<family>.md`) + vosita izohi
(`system_prompts/notes/<tool>.md`). Namunalar: `examples/<tool>/` → `examples/<family>/` → `chat`.
"""

from functools import lru_cache
from pathlib import Path

from app.ai.catalog import TOOLS, family_for

AI_DIR = Path(__file__).parent
SYSTEM_DIR = AI_DIR / "system_prompts"
NOTES_DIR = SYSTEM_DIR / "notes"
EXAMPLES_DIR = AI_DIR / "examples"

LOCALE_NAMES = {
    "uz": "Uzbek (Latin script; use the ʻ apostrophe: oʻ, gʻ)",
    "ru": "Russian",
    "en": "English",
}
KIND_NAMES = {
    "image": "image / picture / logo / illustration",
    "app": "app / website / code / software",
    "design": "design / UI / brand / presentation / layout",
    "video": "video / animation / clip",
    "text": "text / article / post / email / script / message",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


@lru_cache
def system_prompt(ai: str, kind: str = "text") -> str:
    tool = TOOLS[ai]
    dedicated = SYSTEM_DIR / f"{ai}.md"
    if dedicated.exists():
        return _read(dedicated)
    family = family_for(ai, kind)
    base = SYSTEM_DIR / f"{family}.md"
    if not base.exists():
        raise FileNotFoundError(f"system prompt yoʻq: {base.name} ({ai}/{kind})")
    text = _read(base)
    note = NOTES_DIR / f"{ai}.md"
    if note.exists():
        text += f"\n\n## Tool-specific notes: {tool.name}\n{_read(note)}"
    return text


def _read_examples(folder: Path) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if not folder.exists():
        return out
    for f in sorted(folder.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        if "## Input" not in text or "## Prompt" not in text:
            continue
        _, rest = text.split("## Input", 1)
        inp, prm = rest.split("## Prompt", 1)
        out.append((inp.strip(), prm.strip()))
    return out


@lru_cache
def examples(ai: str, kind: str = "text") -> list[tuple[str, str]]:
    """Vosita papkasi → oila papkasi → chat. Har fayl: '## Input' va '## Prompt'."""
    tool = TOOLS[ai]
    candidates = []
    if tool.examples_dir:
        candidates.append(tool.examples_dir)
    candidates.append(family_for(ai, kind))
    candidates.append("chat")
    for name in candidates:
        found = _read_examples(EXAMPLES_DIR / name)
        if found:
            return found
    return []


def examples_block(ai: str, kind: str = "text", limit: int = 6) -> str:
    items = examples(ai, kind)[:limit]
    if not items:
        return ""
    parts = ["<examples>"]
    for i, (inp, prm) in enumerate(items, 1):
        parts.append(
            f'<example n="{i}">\n<input>\n{inp}\n</input>\n<prompt>\n{prm}\n</prompt>\n</example>'
        )
    parts.append("</examples>")
    return "\n".join(parts)


def context_block(context: dict[str, str] | None) -> str:
    if not context:
        return ""
    lines = "\n".join(f"- {k}: {v}" for k, v in context.items())
    return (
        "<user_context>\nKnown facts about this user (use them, do not ask again):\n"
        f"{lines}\n</user_context>"
    )


def locale_name(locale: str) -> str:
    return LOCALE_NAMES.get(locale, LOCALE_NAMES["en"])
