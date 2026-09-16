"""Soʻrovdagi nomlar (brend, loyiha) generate system promptida fakt sifatida talab qilinadi."""

from app.ai import pipeline
from app.ai.prompts import system_prompt


def test_generate_system_has_facts_rule():
    system = pipeline._generate_system("ideogram", "image", "logo", "en", None, None)
    assert "FACTS RULE" in system
    assert "Never replace a given name" in system


def test_image_prompts_distinguish_own_brand_from_style_brands():
    for tool in ("midjourney", "ideogram", "flux", "chatgpt"):
        text = system_prompt(tool, "image")
        assert "OWN brand" in text, tool
