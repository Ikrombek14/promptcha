# Portrait, character, avatar
## Required facts
- subject: who the person or character is (age, gender, role, one defining trait) and whether it is a real likeness or an invented character | ask: Who is the person or character — age, gender, role? Real person or invented? | default: an invented character; no real person likeness
- style: medium (photorealistic portrait, flat vector avatar, 3D cartoon, anime, watercolor illustration, pixel art) | ask: Which style — realistic photo, cartoon, anime, vector? | default: clean flat vector illustration
- usage: where it goes (Telegram/Instagram avatar, presentation, book illustration, game character, mascot) | ask: Where will it be used? | default: profile avatar, square, head and shoulders
- mood: expression and feeling (friendly smile, serious, confident, playful) | ask: What expression or mood? | default: friendly, calm, looking at the camera
- clothing: outfit and cultural details (business casual, chapan and doppi, school uniform, lab coat) | ask: What are they wearing? | default: simple modern clothing in neutral colors
- background: plain color, gradient-free studio, or a simple setting | ask: Plain background or a setting? | default: plain single-color background
## Must include
- Medium first ("A photorealistic studio portrait of…", "A flat vector avatar of…") with the framing (head-and-shoulders, waist-up, full body)
- Subject with age range, gender, skin/hair described neutrally, one defining accessory or trait, and the expression
- Clothing and cultural details with correct English names (chapan robe, doppi cap, atlas silk dress, suzani pattern)
- Lighting and camera in words (soft window light, 85mm lens, shallow depth of field) for photos; line weight and color count for vectors
- Background and format: "square 1:1, centered, face in the upper-middle third"; Midjourney `--ar 1:1 --v 7` plus `--style raw` for photos and `--no blur, distortion, extra fingers, text, watermark`
- No text on the image unless it is a name badge given by the user in quotes
- Explicit "invented character, not a real person" unless the user is describing themselves for a personal avatar
## Quality rules
- One person per prompt; a group needs a separate scene prompt
- Hands rule: hide or simplify hands (crossed arms, hands out of frame) unless the pose needs them; add `--no extra fingers` on Midjourney
- Diversity and locality: describe Central Asian features naturally when the user wants a local look ("a young Uzbek woman with dark hair"), never with stereotypes or costume clichés
- No celebrity likeness, no real politicians, no copyrighted characters; "in the style of" refers to a medium or era ("1970s studio portrait", "Pixar-style 3D" is not allowed — say "stylized 3D cartoon with big eyes and soft shading")
- Avatar rule: face must be readable at 64 px — plain background, high contrast between subject and background, minimal details
- Consistency for a series: fix 5 traits (hair, glasses, outfit color, skin tone, expression) so every image matches; state them as a list
- Length: 40–100 words for natural-language tools; 30–60 words plus parameters for Midjourney
- Ask for 2 variants changing only the expression or the background color
## Avoid
- "Beautiful girl" or "handsome man" with no age, style, clothing or framing
- Requesting a real person's face from a description (deepfake risk) — use "use my reference photo" only if the tool supports it
- Full-body dynamic poses with detailed hands and props for a simple avatar
- Busy backgrounds that fight the face in a small round crop
- Mixing realistic skin with cartoon proportions in one prompt
