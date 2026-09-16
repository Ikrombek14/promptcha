# Product photo and packaging
## Required facts
- product: what exactly the product is, its material, color and size (a jar of honey 500 g, a leather wallet, a box of samsa) | ask: What is the product — material, color, size? | default: the product from the user's text; if unclear, ask
- usage: where the image will be used (marketplace listing on Uzum/Yandex Market, Instagram, menu, packaging mockup, banner) | ask: Where will the photo be used — marketplace, Instagram, menu? | default: marketplace listing, white background, square
- style: shot type (clean white studio, lifestyle scene in use, flat lay, hero shot with props, macro detail) | ask: Clean studio shot or a lifestyle scene? | default: clean studio shot on a plain background, soft light
- brand_name: name or label text that must appear on the product or packaging | ask: Should the brand name or label text be visible? What exactly? | default: no readable text; if given, in quotes exactly as written
- colors: background and accent colors | ask: Which background color? | default: white or light neutral background
- format: aspect ratio | ask: Which format — square, vertical, wide? | default: square 1:1
## Must include
- "photorealistic product photo" (or "packaging design mockup") as the medium in the first sentence
- Product described with material, texture, color and exact count ("one jar", "three samsa on a plate")
- Camera angle and distance (45-degree three-quarter view, straight-on, overhead flat lay, close-up macro)
- Lighting in words (soft diffused studio light, natural window light, golden hour) and shadow rule (soft shadow / no shadow)
- Background and props: plain color or 1–2 context props only, named concretely (a wooden board, a piece of non bread)
- Format in words and, for Midjourney, `--ar 1:1 --v 7 --style raw --no text, watermark, hands, blur`
- Text handling: label text in quotes only for Ideogram/GPT Image/Flux; for Midjourney, "blank label" and `--no text`
## Quality rules
- Marketplace rule: pure white background, product fills 70–85% of the frame, no props, no text, square format — say it explicitly when usage is a marketplace listing
- Food: describe freshness cues (steam, glistening oil, crumbs, condensation) and correct dish names (plov, samsa, non, manti); never "traditional food"
- One product, one hero angle per prompt; variants change only the angle or the background
- No invented claims on packaging ("organic", "100% natural", awards) — only text the user gave
- Realism cues: "shot on a 85mm lens, shallow depth of field, sharp focus on the label" for photos; "8k" only for photos or renders
- Packaging design: state the package type and size (a 500 g kraft pouch, a 10×10 cm box), the front-panel layout (logo top, product name center, weight bottom) and the palette (max 3 colors)
- Ban stacked quality tags and "professional photography" — specify light, lens and angle instead
- Length: 40–100 words for natural-language tools, 30–60 words plus parameters for Midjourney
## Avoid
- Lifestyle scenes with people, hands and clutter when the user needs a catalog photo
- Rendering readable label text in Midjourney and expecting the brand name to be right
- Several products in one shot when each needs its own listing photo
- Inventing the product's size, flavor, ingredients or price
- Generic "beautiful product photo" without angle, light, background and format
