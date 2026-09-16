# Poster, flyer, banner, ad creative
## Required facts
- purpose: what the poster promotes (an event, a sale, an opening, a course enrollment) and the one action it should cause | ask: What is the poster for, and what should the viewer do? | default: promote [tadbir/taklif], the viewer contacts [telefon]
- format: platform and size (Instagram post 1:1 or 4:5, story 9:16, A4/A3 print, Telegram banner 16:9, billboard) | ask: Where will it be shown — Instagram post, story, print A4, banner? | default: Instagram post, 4:5 vertical
- text: the exact headline (≤6 words), optional subline, date/price and contact, in the audience's language | ask: What exact text must appear — headline, date, price, contact? | default: headline only as [sarlavha] placeholder; no invented dates or prices
- style: visual mood (bold and loud, clean minimal, festive, premium, playful for kids) | ask: What mood — bold, minimal, festive, premium? | default: clean, bold headline, one strong visual, lots of empty space
- colors: 2–3 colors or brand colors | ask: Which colors? | default: one strong accent on a neutral background
- subject: the main visual (a product, a person, an icon, an abstract shape) | ask: What should be the main picture — a product, a person, a scene? | default: one product or object related to the offer, centered
## Must include
- Format stated as both words and ratio ("a vertical poster 4:5"; Midjourney `--ar 4:5 --v 7`)
- Whether text is rendered by the tool or added later: Ideogram, GPT Image and Flux render text — give every word in quotes with placement and font feel; Midjourney — describe the layout with "empty space at the top for a headline" and `--no text`
- One dominant visual subject and its position; the headline zone described (top third, bottom band)
- Named palette (max 3 colors) and contrast rule ("headline in high contrast against the background")
- Style as a medium ("flat vector illustration", "bold retro print", "studio photo with a color background"), never a brand or artist
- Reading distance: for print, "large headline readable from 3 meters"; for social, "readable on a phone screen"
- What to exclude: clutter, extra objects, watermarks, small text
## Quality rules
- Text hierarchy fixed with counts: 1 headline (≤6 words), 1 subline (≤12 words), 1 contact/date line — nothing more on the image
- Language of the rendered text matches the audience (Uzbek Latin or Russian), spelled exactly as the user gave it; the prompt itself stays in English
- For sales/offers, the number must come from the user ("20% off" only if given); otherwise [chegirma] and the model must not invent it
- Composition rule: 60% visual, 40% text zones; state where empty space goes so the text does not overlap the subject
- Story/Reels format: keep the top and bottom 15% free of key elements (UI overlays)
- Ask for 2 variants that differ in one thing (color scheme or layout), not in everything
- Cultural context: local festive elements described precisely (suzani pattern border, Navroʻz sumalak, tulips) instead of "Uzbek decoration"
- Length: 40–100 words for natural-language tools; 30–60 words plus parameters for Midjourney
## Avoid
- Long paragraphs of text on the image — a poster is not an article
- Inventing dates, prices, discounts, phone numbers or addresses
- Asking Midjourney to render a full sentence of Uzbek text and expecting it to be correct
- Mixing three styles (photo + cartoon + 3D) in one creative
- Using competitors' or famous brands' look as the style reference
