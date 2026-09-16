# Logo
## Required facts
- brand_name: the exact name to appear in the logo, spelled as the user writes it | ask: What is the exact brand name (spelling matters)? | default: [brend nomi] — never a generic "BRAND"
- business: what the business does and its one defining trait (a bakery, a kids' English center, a taxi service) | ask: What does the business do? | default: taken from the user's text; if absent, ask
- style: logo type and feel (flat minimal, emblem/badge, wordmark only, mascot, geometric, hand-drawn) | ask: Which style — minimal flat, emblem, wordmark, or mascot? | default: flat minimal vector, monoline
- colors: 1–3 colors named in words | ask: Which colors (up to 3)? | default: two colors: one dark ink tone and one warm accent, no gradients
- symbol: the object or idea the mark should show, if the user has one | ask: Is there a symbol or object you want in the mark? | default: one simple object tied to the business (a non bread for a bakery), chosen by the model
- usage: where the logo will live (Instagram avatar, sign, packaging, app icon) | ask: Where will it be used first? | default: Instagram profile picture and a Telegram avatar (small, round crop)
## Must include
- The word "logo" plus the medium: "flat vector logo", "emblem logo", "wordmark" — first sentence
- The brand name in quotes exactly as given, and where it sits (below the mark, inside the badge, wordmark only)
- Exactly one simple symbol described concretely (shape, strokes, count) — or "no symbol, wordmark only"
- Named color palette (max 3) and "no gradients, no shadows, no 3D" unless the style asks for it
- Square format, centered, plain single-color background, generous margins; nothing else in the frame
- Tool syntax: Midjourney → `--ar 1:1 --v 7 --style raw --no photorealistic, 3d render, shadows, gradient` (add `--no text` when the name should not be rendered); natural-language tools → "a square image" in words; Ideogram/GPT Image/Flux may render the name, Midjourney is unreliable for text
- Font feel for the wordmark (geometric sans-serif, rounded sans, classic serif), stated in words
## Quality rules
- Readability test in the prompt: "must be readable at 32 px and work in one color" — this forces a simple mark
- One idea per logo: one symbol, one wordmark, one palette; no scene, no background objects
- If the tool cannot render text reliably (Midjourney), instruct to produce the mark only and add `--no text`, or put the name in quotes with `--style raw` and expect to fix typography later
- Cultural items get correct English descriptors (suzani motif, ikat pattern, tandoor, non bread, chapan, doppi cap) rather than "Uzbek style"
- No brand names or artists as style references; styles are media or movements ("Swiss modernist", "Bauhaus geometric", "monoline line art")
- Prompt length: 30–60 words before parameters (Midjourney) or 2–4 sentences (natural-language tools)
- Ask for variants by changing one element only (mark vs wordmark, palette A vs B) — the rest identical, so results are comparable
- Never invent a slogan or tagline; if the user gave one, put it in quotes; otherwise omit
## Avoid
- Generic "LOGO" or "BRAND" placeholders when the user gave the name
- Several symbols crammed together (a cup + a book + a sun + a map) — pick one
- Quality tag stacks ("8k, masterpiece, ultra detailed") on a flat logo
- Photorealistic renders, mockups on cups or walls, backgrounds with scenes
- Copying a known brand's mark or asking for "like Nike/Starbucks"
