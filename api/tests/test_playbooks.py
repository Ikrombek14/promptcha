"""Playbook fayllari (system_prompts/playbooks/<kind>/<archetype>.md) va loader."""

from app.ai import prompts
from app.ai.prompts import PLAYBOOK_SECTIONS, PLAYBOOKS_DIR, _parse_playbook

SAMPLE = """# Social post
## Required facts
- audience: who reads it | ask: Who is the post for? | default: general local audience
- goal: what the post should achieve | ask: What should readers do? | default: engagement
## Must include
- one hook line
- one call to action
## Quality rules
- word count as a number
## Avoid
- hashtags spam
"""


def test_parse_playbook_sections_and_facts():
    pb = _parse_playbook("text", "post", SAMPLE)
    assert pb.title == "Social post"
    assert [f.id for f in pb.facts] == ["audience", "goal"]
    assert pb.facts[0].ask == "Who is the post for?"
    assert pb.facts[0].default == "general local audience"
    assert pb.must_include == ("one hook line", "one call to action")
    assert pb.quality_rules == ("word count as a number",)
    assert pb.avoid == ("hashtags spam",)
    assert not pb.empty


def test_every_kind_has_general_and_files_are_well_formed():
    for kind in prompts.KIND_NAMES:
        assert "general" in prompts.archetypes(kind), kind
        assert (PLAYBOOKS_DIR / kind / "general.md").exists(), kind
    for path in PLAYBOOKS_DIR.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        heads = [line[3:].strip() for line in text.splitlines() if line.startswith("## ")]
        assert heads == list(PLAYBOOK_SECTIONS), path
        pb = _parse_playbook(path.parent.name, path.stem, text)
        assert pb.facts, f"{path}: Required facts boʻsh"
        assert all(f.default for f in pb.facts), f"{path}: default boʻsh"
        assert pb.must_include and pb.quality_rules, path


def test_missing_archetype_falls_back_to_general():
    pb = prompts.playbook("text", "nonexistent")
    assert pb.archetype == "general"
    assert prompts.normalize_archetype("text", "nonexistent") == "general"
    assert prompts.normalize_archetype("image", None) == "general"


def test_blocks_render():
    pb = _parse_playbook("text", "post", SAMPLE)
    facts = prompts.playbook_facts_block(pb)
    assert "<required_facts>" in facts and "audience:" in facts
    rules = prompts.playbook_rules_block(pb)
    assert '<playbook title="Social post">' in rules
    assert "Must include:" in rules and "Avoid:" in rules
    assert "<rubric>" in prompts.RUBRIC and "facts_kept" in prompts.RUBRIC
