# Article: blog post, SEO text, long-form content
## Required facts
- topic: the exact subject and the angle (not "about coffee" but "how to choose a coffee machine for a small cafe under $500") | ask: What exactly is the article about, from what angle? | default: the user's topic narrowed to one practical question
- audience: who reads it and what they already know (beginners, business owners, students, parents) | ask: Who is the reader and what do they already know? | default: beginners in Uzbekistan with no prior knowledge
- goal: what the article should achieve (rank on Google/Yandex, educate, sell a service, build trust on a personal blog) | ask: What is the article for — SEO traffic, teaching, or selling something? | default: educate and build trust; no hard selling
- length: target word count | ask: How long should it be? | default: 700–1000 words
- keywords: main keyword and 2–4 secondary ones (for SEO texts) | ask: Which search phrases should it target? | default: derive 1 main phrase from the topic and mark it as [asosiy kalit soʻz] for the user to confirm
- language: language and script of the article | ask: Which language — Uzbek, Russian or English? | default: Uzbek (Latin)
## Must include
- One-sentence thesis or reader promise the article must deliver ("after reading, the reader can …")
- Outline with H2/H3 headings, each with the number of paragraphs or bullets expected, and the total word count
- Intro rule: first paragraph under 60 words, states the reader's problem and what the article gives; no history lesson
- At least one real, local example or worked scenario per main section (a shop in Tashkent, a student preparing for DTM, a Telegram channel)
- Meta title (under 60 characters) and meta description (under 155 characters) when the goal is SEO
- Explicit answer language plus reading level ("simple sentences, no academic vocabulary")
- Source rule: facts, statistics and prices must be marked as [manba] / [raqam] unless the user provided them, or the model must say it cannot verify
## Quality rules
- Keyword placement as a checklist: main keyword in H1, first 100 words, one H2 and the conclusion; no keyword stuffing (max 1–2% density)
- Structure for scanning: no paragraph over 4 sentences, one list or table per 300 words, a short summary (3 bullets) at the top or bottom
- Require "explain like to a smart 14-year-old" when the audience is beginners; define every term the first time it appears
- Ban filler phrases and hype: "in today's fast-paced world", "hozirgi zamonaviy dunyoda", "eng yaxshi", "revolutionary"
- Ask for a specific closing: a practical next step or checklist, not a generic "hope this helps"
- For comparison or "best X" articles: fixed criteria list (3–5 criteria) applied to every item, in a table
- If the model lacks reliable data for a claim, it must write "[tekshirish kerak]" instead of guessing
- Optional final section: 3–5 FAQ questions with two-sentence answers (good for SEO and for beginners)
## Avoid
- Generic outlines that fit any topic (Introduction / Benefits / Conclusion) without concrete section titles
- Inventing statistics, study names, prices or dates
- Requesting several articles or an article plus social posts in one prompt
- Long academic intros and history before the useful part
- Word count left unspecified so the model writes 300 or 3000 words at random
