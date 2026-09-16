# Social media post or ad copy (Telegram, Instagram, Facebook)
## Required facts
- platform: where the post will be published (Telegram channel, Instagram caption, Facebook, Threads) | ask: Where will you post it? | default: Telegram channel, read on a phone
- goal: the one action the reader should take (order, visit, sign up, save, share, learn about a new item) | ask: What should the reader do after reading? | default: contact or visit the business via [telefon] / [manzil]
- audience: who reads it (age, city, situation, e.g. "young mothers in Tashkent", "students") | ask: Who is this post for? | default: local customers in Uzbekistan, 20–45, reading on a phone
- tone: voice of the post (friendly, playful, formal, premium, urgent) | ask: What tone — friendly, formal or playful? | default: friendly, everyday Uzbek (Latin)
- offer: the concrete news or value (new menu, 20% discount until Friday, opening, free delivery) | ask: What is the news or offer you announce? | default: [taklif] placeholder; never invent a discount or price
- brand_name: name of the business/product/channel | ask: What is the business or channel name? | default: [brend nomi]
## Must include
- Exact platform and reading context ("a Telegram channel post read on a phone at lunchtime")
- Word count range (Telegram 60–120, Instagram caption 80–150, ad copy 40–80) and paragraph structure (short lines, blank line between paragraphs)
- First line is a hook that creates interest or appetite — no "Hurmatli mijozlar", no greeting as the opener
- Exactly one call to action at the end, with [telefon] / [manzil] / [havola] placeholders where unknown
- Answer language and script stated explicitly ("Answer in Uzbek (Latin script)" or Russian), matching the audience
- Emoji and hashtag limits as numbers (e.g. "max 3 emojis", "no hashtags" for Telegram, "3–5 relevant hashtags" for Instagram)
- Number of variants to produce (2 variants with a one-word label each: playful / calm)
## Quality rules
- Two quantities minimum in the prompt: length (words) and count (variants, dishes/products named, emojis)
- Name 2–3 concrete product/offer details the post must mention; if the user gave none, insert [mahsulot 1], [mahsulot 2] and tell the model to keep them as placeholders
- Ban "praise words" by list: no "eng zoʻr", "ajoyib", "professional", "sifatli", "best", "amazing" — show a specific benefit instead
- Facts rule: prices, dates, discounts, addresses come only from the user; anything missing stays as a [placeholder], never a guess
- Use a named copywriting frame where it helps (AIDA or PAS) and say which one in one line; for Instagram, the first 125 characters must carry the hook because the caption is cut there
- Ask for a plain-text answer ready to paste (no markdown headings, no bold inside the post itself)
- If the post is an ad (promo/discount), require an explicit deadline or condition line ([sana] gacha / [shart]) so the offer is concrete
- Instruct: "If a key fact (name, offer, contact) is missing, ask me before writing"
## Avoid
- Generic role ("you are a marketer") — name the platform, the niche and the city in the role
- Inventing prices, discounts, opening hours, addresses or dish names
- Bundling several deliverables (post + story + ad + slogan) into one prompt — one post, optional 2 variants
- Corporate or translated-from-Russian tone ("Hurmatli mijozlar, sizlarni xabardor qilamiz")
- Vague "make it engaging" instead of hook, CTA, length and emoji limits
