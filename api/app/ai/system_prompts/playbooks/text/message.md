# Message: email, letter, proposal, reply to a customer
## Required facts
- recipient: who receives it and your relation to them (a client, a supplier, a boss, an official, a complaining customer) | ask: Who is the message for and what is your relationship? | default: a customer of a small business, addressed politely as "siz"
- goal: the one outcome you want (get a meeting, get paid, apologise and keep the client, get approval, decline politely) | ask: What should happen after they read it? | default: a clear reply or next step from the recipient
- situation: the concrete facts — what happened, dates, amounts, what was promised | ask: Briefly, what is the situation (what happened, when, how much)? | default: [holat] placeholder; the model must not invent events or amounts
- tone: formal / neutral / warm / firm | ask: How formal should it sound? | default: polite and neutral, plain language
- channel: email, Telegram message, WhatsApp, official letter on paper | ask: Where will you send it — email, Telegram or a paper letter? | default: Telegram / messenger, short
- language: the language and script the recipient reads | ask: Which language should the message be in? | default: Uzbek (Latin)
## Must include
- Sender and recipient roles with the relationship and the concrete situation in the Context section (facts from the user, [placeholders] for the rest)
- Length as a number: messenger 50–100 words, email 100–180 words, official letter 150–250 words
- A reply structure named in the prompt — for complaints: Understand | Apologise | Solve | Next step; for proposals: Who we are | What we offer | Why it fits you | Next step; for requests: Context | Ask | Deadline | Thanks
- Exactly one ask or next step at the end, with a specific date or time window ([sana], "by Friday")
- Answer language, script and level of formality stated explicitly (siz vs. sen, "Hurmatli" vs. first name)
- Subject line for emails (max 8 words) or the first line for messengers
## Quality rules
- The message must acknowledge the recipient's side in the first two sentences (their problem, their time, their previous message) before stating the ask
- No blame, no excuses list: for apologies, one sentence of apology, then the fix and the compensation or timeline as concrete items
- Numbers and dates must be exact and taken from the user; if unknown, keep [summa], [sana] and instruct the model to leave them as placeholders
- Ban jargon and template phrases: "ushbu xat orqali", "sizni xabardor qilamiz", "hurmat bilan qolamiz" unless the user asked for an official letter style
- Require 2 variants when tone is uncertain (e.g. "one warmer, one more formal"), otherwise one clean version
- For declines or firm messages: state the decision in the first three lines, give one reason, offer one alternative
- End the prompt with: "If the situation or the ask is unclear, ask me one question before writing"
## Avoid
- Writing a full multi-page proposal when the user needs a five-line reply
- Inventing what the recipient said or promised, or the amounts involved
- Several asks in one message (meeting + payment + feedback) — one ask per message
- Over-apologising or flattery ("we are the best company") instead of the concrete solution
- Mixing formal and informal address in the same message
