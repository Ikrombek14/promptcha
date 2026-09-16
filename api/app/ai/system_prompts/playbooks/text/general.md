# General text task
## Required facts
- goal: what the text is for and what should happen after it is read | ask: What is this text for — what should it achieve? | default: a clear, useful answer the user can use directly
- audience: who will read the result and their language | ask: Who will read it, and in which language? | default: Uzbek-speaking reader in Uzbekistan, beginner level, Uzbek (Latin)
- length: expected size of the answer | ask: How long should the answer be? | default: 150–300 words, short paragraphs or a list
## Must include
- One clearly named deliverable (a list, a text, a table, an answer) — the Task line says exactly what and how many
- Length as a number and the output format (bullets, numbered list, table, plain paragraphs)
- Answer language and script stated explicitly ("Answer in Uzbek (Latin script)")
- The user's facts kept exactly as given; missing facts as [placeholders], never guessed
- Tone and reading level in one line ("plain language, no jargon, define terms")
## Quality rules
- At least two measurable requirements (length, count of items, number of variants or examples)
- Specific role with domain and locale ("a Tashkent-based … who works with small businesses"), not "helpful assistant"
- At least one concrete example or local reference the answer must include
- Constraint line: what not to include (hype words, generic advice, unrelated topics)
- "Not enough information" rule: if a fact is missing, the model asks one question or marks [aniqlashtirish kerak] instead of inventing
- If the request is a list or recommendations, require priority order (most important first) and a one-line reason per item
## Avoid
- Several unrelated tasks in one prompt — pick the main one, mention the rest as "later, if asked"
- Vague quality words ("good", "professional", "engaging") without a measurable rule
- Inventing names, numbers, dates or prices on the user's behalf
- Long preamble or theory before the actual deliverable
