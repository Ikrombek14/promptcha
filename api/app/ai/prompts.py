"""system_prompts/*.md va examples/*/ fayllarini oʻqish. Kod oʻzgarmaydi — fayllar yaxshilanadi.

Prompt uslubi: vosita uchun maxsus fayl boʻlsa (`system_prompts/<tool>.md`, masalan midjourney,
claude) — oʻsha; boʻlmasa oila fayli (`system_prompts/<family>.md`) + vosita izohi
(`system_prompts/notes/<tool>.md`). Namunalar: `examples/<tool>/` → `examples/<family>/` → `chat`.
"""

from dataclasses import dataclass
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


def examples_block(ai: str, kind: str = "text", limit: int = 3) -> str:
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


# --------------------------------------------------------------------------- playbooks
# system_prompts/playbooks/<kind>/<archetype>.md — vazifa arxetipi uchun bizning qoidalarimiz.
# Format: "# Title", keyin aynan toʻrt boʻlim: Required facts, Must include, Quality rules, Avoid.
# Required facts qatori: "- id: what | ask: how to ask | default: assumed value".

PLAYBOOKS_DIR = SYSTEM_DIR / "playbooks"
PLAYBOOK_SECTIONS = ("Required facts", "Must include", "Quality rules", "Avoid")


@dataclass(frozen=True)
class Fact:
    id: str
    what: str
    ask: str
    default: str


@dataclass(frozen=True)
class Playbook:
    kind: str
    archetype: str
    title: str
    facts: tuple[Fact, ...]
    must_include: tuple[str, ...]
    quality_rules: tuple[str, ...]
    avoid: tuple[str, ...]

    @property
    def empty(self) -> bool:
        return not (self.facts or self.must_include or self.quality_rules)


def _parse_fact(line: str) -> Fact | None:
    # "- audience: who reads it | ask: Who is it for? | default: general public"
    head, *rest = [p.strip() for p in line.split("|")]
    if ":" not in head:
        return None
    fid, what = head.split(":", 1)
    ask = default = ""
    for p in rest:
        if p.lower().startswith("ask:"):
            ask = p[4:].strip()
        elif p.lower().startswith("default:"):
            default = p[8:].strip()
    fid = fid.strip().lower().replace(" ", "_")
    return Fact(fid, what.strip(), ask, default) if fid else None


def _parse_playbook(kind: str, archetype: str, text: str) -> Playbook:
    title = ""
    sections: dict[str, list[str]] = {s: [] for s in PLAYBOOK_SECTIONS}
    current: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("# ") and not title:
            title = line[2:].strip()
        elif line.startswith("## "):
            name = line[3:].strip()
            current = name if name in sections else None
        elif line.startswith("- ") and current:
            sections[current].append(line[2:].strip())
    facts = tuple(f for f in (_parse_fact(x) for x in sections["Required facts"]) if f)
    return Playbook(
        kind=kind,
        archetype=archetype,
        title=title or archetype,
        facts=facts,
        must_include=tuple(sections["Must include"]),
        quality_rules=tuple(sections["Quality rules"]),
        avoid=tuple(sections["Avoid"]),
    )


@lru_cache
def archetypes(kind: str) -> tuple[str, ...]:
    """Shu kind uchun mavjud playbook nomlari (fayllardan); `general` doim oxirida."""
    folder = PLAYBOOKS_DIR / kind
    if not folder.exists():
        return ("general",)
    names = sorted(p.stem for p in folder.glob("*.md") if p.stem != "general")
    return (*names, "general")


@lru_cache
def playbook(kind: str, archetype: str = "general") -> Playbook:
    """Arxetip fayli → yoʻq boʻlsa `general` → u ham yoʻq boʻlsa boʻsh playbook (pipeline ishlayveradi)."""
    for name in (archetype, "general"):
        path = PLAYBOOKS_DIR / kind / f"{name}.md"
        if path.exists():
            return _parse_playbook(kind, name, _read(path))
    return Playbook(kind, "general", "general", (), (), (), ())


def normalize_archetype(kind: str, archetype: str | None) -> str:
    a = (archetype or "general").strip().lower()
    return a if a in archetypes(kind) else "general"


def archetype_guide() -> str:
    """Classifier uchun: har kind'ning arxetiplari va sarlavhalari."""
    lines = []
    for kind in KIND_NAMES:
        items = ", ".join(f"{a} ({playbook(kind, a).title})" for a in archetypes(kind))
        lines.append(f"- {kind}: {items}")
    return "\n".join(lines)


def playbook_facts_block(pb: Playbook) -> str:
    if not pb.facts:
        return ""
    lines = [f"- {f.id}: {f.what} | ask: {f.ask} | default: {f.default}" for f in pb.facts]
    return "<required_facts>\n" + "\n".join(lines) + "\n</required_facts>"


def playbook_rules_block(pb: Playbook) -> str:
    if pb.empty:
        return ""
    parts = [f'<playbook title="{pb.title}">']
    if pb.must_include:
        parts.append("Must include:\n" + "\n".join(f"- {x}" for x in pb.must_include))
    if pb.quality_rules:
        parts.append("Quality rules:\n" + "\n".join(f"- {x}" for x in pb.quality_rules))
    if pb.avoid:
        parts.append("Avoid:\n" + "\n".join(f"- {x}" for x in pb.avoid))
    parts.append("</playbook>")
    return "\n".join(parts)


def brief_block(brief_json: str) -> str:
    return (
        "<brief>\nThe prompt MUST be built from this brief. Every fact in it appears in the "
        "prompt; every id in `missing` becomes a [placeholder]; constraints become explicit "
        f"requirements.\n{brief_json}\n</brief>"
    )


# Umumiy rubrika — generate (oʻz-oʻzini tekshirish) va review (baholash) bir xil mezonlar bilan
RUBRIC = chr(10).join(
    [
        "<rubric>",
        "1. task_clear — one precise task and deliverable.",
        "2. facts_kept — every user fact (names, numbers, places, products) kept verbatim; nothing invented; only truly missing facts are [placeholders].",
        "3. measurable — length, counts, format as numbers/shapes, not adjectives.",
        "4. audience_tone — who it is for and the answer language/tone are explicit.",
        "5. constraints — what to avoid, limits (budget, time, platform), ask-before-guessing when something important is unknown.",
        "6. no_filler — no generic phrases, no duplicated sections, matches the tool's syntax.",
        "</rubric>",
    ]
)
