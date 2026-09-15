from app.ai import prompts
from app.ai.catalog import TOOLS, family_for


def test_every_tool_kind_has_system_prompt():
    for tool in TOOLS.values():
        for kind in tool.kinds:
            text = prompts.system_prompt(tool.id, kind)
            assert len(text) > 200, (tool.id, kind)
            assert "## Output format" in text, (tool.id, kind)


def test_shared_family_prompts_get_tool_notes():
    text = prompts.system_prompt("gemini", "text")
    assert "Tool-specific notes: Gemini" in text
    # Maxsus fayli borlar oila + izohni emas, oʻz faylini oladi
    assert "Midjourney v7" in prompts.system_prompt("midjourney", "image")


def test_every_tool_kind_has_examples():
    for tool in TOOLS.values():
        for kind in tool.kinds:
            ex = prompts.examples(tool.id, kind)
            assert len(ex) >= 2, (tool.id, kind, family_for(tool.id, kind))
            for inp, prm in ex:
                assert inp and prm, tool.id


def test_examples_block_is_tagged():
    block = prompts.examples_block("midjourney", "image", limit=2)
    assert block.startswith("<examples>")
    assert block.count("<example n=") == 2


def test_context_block_empty_and_filled():
    assert prompts.context_block(None) == ""
    assert prompts.context_block({}) == ""
    block = prompts.context_block({"industry": "restoran"})
    assert "industry: restoran" in block
