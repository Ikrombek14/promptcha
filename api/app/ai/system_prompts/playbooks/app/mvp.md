# MVP: new app, website or bot from scratch
## Required facts
- problem: what the app does for whom, in one sentence (a Telegram bot that takes cake orders for a home baker; a site where a tutor publishes a schedule) | ask: What should the app do, and for whom? | default: derive one sentence from the user's text; if the purpose is unclear, ask
- users: who uses it and on what device (customers on a phone, the owner on a laptop, students via Telegram) | ask: Who will use it, and on which device? | default: customers on a phone (mobile-first), the owner on any device
- core_features: the 3–5 things the first version must do | ask: What are the 3–5 must-have features for the first version? | default: the model proposes 3–5 MVP features from the problem and lists everything else as "later"
- platform: web site, web app, Telegram bot, mobile app | ask: Should it be a website, a web app, a Telegram bot or a mobile app? | default: mobile-first web app (a Telegram bot when the users live in Telegram)
- language: language of the UI text | ask: Which language for the interface? | default: Uzbek (Latin)
- data: what must be stored (orders, users, products, bookings) and any existing data source (Google Sheet, Excel) | ask: What data should it keep — orders, products, users? Any existing spreadsheet? | default: a minimal data model proposed by the model from the features
## Must include
- Goal line: one sentence with the user type and the outcome
- Stack decision stated (beginner-friendly default named explicitly, e.g. Next.js + TypeScript + Tailwind + SQLite/Prisma; Python + aiogram + SQLite for a Telegram bot; plain HTML/CSS/JS for a static site)
- MVP features as a numbered list of 3–7 testable sentences, each with an acceptance criterion ("the owner sees new orders within 5 seconds of submission")
- Data model: entities and key fields; pages/screens or bot commands with one line each
- Constraints: UI language, mobile-first, no auth/payments unless required, secrets in `.env`, small files, error and empty states for every list
- Steps: 3–6 numbered steps for the agent, ending with "run it locally and tell me how to start it"; tests for the core flow
- Out of scope line: what is explicitly postponed (payments, admin analytics, multi-language)
## Quality rules
- Scope cap: MVP under 7 features, under 6 screens; anything beyond goes to "Out of scope (for now)"
- Every feature must be verifiable: include a "Done when" phrase or a short acceptance test per feature
- No placeholders in stack, entities or routes; [placeholders] only for business facts (brand name, phone, address)
- Local realities: phone-number-based contact instead of email signup, Uzbek/Russian UI, soʻm currency formatting, Telegram as the notification channel, hosting on a cheap VPS or free tier
- Require the agent to work in small commits/steps and to stop and ask if a requirement is ambiguous — one line in the prompt
- Ask for a README with run instructions and a `.env.example`; no deployment, no payment integration in the first prompt
- Error handling minimum: validation messages in the UI language, empty states, one loading state — stated as a requirement
- Length: 150–350 words; markdown sections in the family order
## Avoid
- "Build me an app like Uzum/Yandex Go" with no feature list — one concrete problem, few features
- Asking for auth, payments, admin panels, analytics and multi-language in version one
- Leaving the stack to the agent when the user is a beginner — decide and state it
- Ambiguous features ("user-friendly", "modern design") with no acceptance criterion
- Several apps or a whole platform in one prompt
