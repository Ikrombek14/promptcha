# General image
## Required facts
- subject: the one main thing to show and what it is doing | ask: What is the main subject of the image? | default: the object or scene from the user's text, one subject only
- style: medium (photo, flat vector, illustration, 3D) | ask: Which style — realistic photo, vector, illustration, 3D? | default: clean digital illustration
- usage: where it goes and therefore the format (Instagram 1:1/4:5, story 9:16, web 16:9, print) | ask: Where will you use it? | default: Instagram post, square 1:1
## Must include
- Medium and subject in the first sentence
- Details: materials, colors (named palette, max 3–4), mood, environment, lighting
- Composition and format: background, subject position, aspect ratio in words; Midjourney `--ar` + `--v 7` (+ `--style raw` for photos, `--no text, watermark`)
- Text rule: exact text in quotes only for Ideogram/GPT Image/Flux; otherwise "no text"
- What to exclude, phrased concretely (no extra objects, no clutter, no gradients)
## Quality rules
- One subject, one style, one palette per prompt
- The user's own names, brands and objects kept exactly; missing facts as [placeholders], never a generic "BRAND"
- Style references are media or movements, not artists, studios or brands
- Uzbek cultural items get precise English descriptors (suzani, ikat, tandoor, non, chapan, Registan)
- Length: 40–100 words natural language, or 30–60 words plus parameters for Midjourney; no quality tag stacks
- Variants: change one element (palette, angle, background) at a time
## Avoid
- Vague adjectives ("beautiful", "high quality", "professional") instead of light, angle, material
- Long sentences of text expected to be rendered correctly by any tool
- Several unrelated images requested in one prompt
- Inventing brand names, slogans or product details
