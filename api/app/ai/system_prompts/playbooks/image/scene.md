# Scene: illustration, landscape, concept art
## Required facts
- subject: the main thing in the scene and what it is doing (a boy and a camel in the desert, Registan at sunrise, a cozy cafe interior) | ask: What is the main subject and what is happening? | default: one clear subject from the user's text, placed in a simple setting
- style: medium (watercolor, flat vector, oil painting, photorealistic, 3D render, pixel art, children's book illustration) | ask: Which style — watercolor, vector, realistic photo, 3D? | default: soft digital illustration with a limited palette
- mood: feeling and time of day/weather (calm morning, festive evening, dramatic storm) | ask: What mood and time of day? | default: warm, calm, golden-hour light
- usage: what the image is for (book page, presentation, website hero, wallpaper, print) | ask: Where will it be used? | default: website or presentation image, wide 16:9
- colors: palette in 2–4 named colors | ask: Which colors dominate? | default: 3-color palette chosen to fit the mood, stated in the prompt
- format: aspect ratio | ask: Which format — wide, square, vertical? | default: wide 16:9
## Must include
- Medium and subject in the first sentence ("A watercolor illustration of…", "A photorealistic wide shot of…")
- One main subject with a concrete action, then 2–3 secondary elements as background, in hierarchy order
- Setting with correct local names when Uzbek (Registan square, Chorsu bazaar, tandoor, plov in a kazan, saxaul shrubs, Tian Shan foothills)
- Light and time of day, weather, and a named palette
- Composition: camera distance (wide/medium/close), subject position (left third, centered), horizon line, foreground/background depth
- Format in words plus Midjourney `--ar 16:9 --v 7` (and `--no text, watermark`; `--style raw` for photorealism)
- "No text" unless the user gave a caption in quotes
## Quality rules
- Limit the inventory: max 5 named objects in the scene; everything else described as texture or atmosphere
- Physically plausible detail (light direction consistent, shadows match the sun position) — say "consistent light from the left" when it matters
- Style references are media or movements ("Soviet-era travel poster style", "ukiyo-e woodblock", "Ghibli-like" is not allowed — say "hand-painted anime background with soft clouds"), never living artists or studios
- For children's illustrations: friendly shapes, no scary details, characters with simple faces, bright but limited palette
- For concept art and interiors: name materials (brick, walnut wood, brass) and 1–2 focal objects; state the viewpoint (eye level, from the doorway)
- Series consistency: if the user needs several scenes, fix style, palette and character traits in one line reused across prompts
- Length: 40–100 words for natural-language tools; 30–60 words plus parameters for Midjourney
- No stacked quality tags; "highly detailed" at most once and only for realistic media
## Avoid
- Listing ten objects with equal weight so the image has no focal point
- "Uzbek style" or "oriental" without naming the actual objects and patterns
- Readable signs, long text or specific fonts inside the scene
- Mixing two incompatible media in one prompt (watercolor + 3D render)
- Famous artworks, characters or brands as the reference
