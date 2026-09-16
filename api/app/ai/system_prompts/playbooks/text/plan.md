# Plan: strategy, roadmap, business or study plan
## Required facts
- goal: the measurable target and its deadline (e.g. "100 orders a month by December", "pass IELTS 6.5 in 4 months") | ask: What exactly do you want to reach, by when? | default: a concrete target the model must ask for; if not given, use [maqsad] and [muddat] and instruct the model to ask first
- current_state: where things are now, with numbers (current customers, revenue, level, hours available per day) | ask: What is the situation now — the key numbers? | default: [hozirgi holat] placeholder; the model must not assume numbers
- resources: budget, people, time per week, tools already available | ask: What budget, time and people do you have? | default: very small budget (under [summa] soʻm), one person, part-time
- horizon: the planning period (2 weeks, 1 month, 3 months, 1 year) | ask: For what period is the plan? | default: 30 days, split into weeks
- constraints: what must not be done or cannot change (no loans, no hiring, no ads budget, only Telegram/Instagram) | ask: Any limits — things you cannot or will not do? | default: no loans, no hiring, low-cost channels only
- language: language of the answer | ask: Which language should the plan be in? | default: Uzbek (Latin), plain language
## Must include
- The goal stated as one measurable sentence with a number and a date
- Current state with the user's real numbers (or [placeholders]) so the gap is visible
- Phases or weeks with dates and 2–4 concrete actions each; every action starts with a verb and names who does it
- One KPI per phase and how it is measured (where the number comes from: sales notebook, Instagram insights, a test score)
- Priority rule: mark the 20% of actions that give 80% of the result; label them "first"
- Risks section: top 3 risks, an early warning sign for each, and a Plan B
- Format instruction: a table (Week | Actions | KPI | Owner) plus a short summary of 3 bullets at the top
## Quality rules
- Every step must be doable within the stated resources; the prompt asks the model to drop anything that needs more budget or people than given
- Name a fitting framework in one line and use it for structure: SMART for the goal, reverse planning from the deadline, OKR for teams, Business Model Canvas for a new business, Pomodoro/spaced repetition for study plans
- Require realism for Uzbekistan: local channels (Telegram, Instagram, word of mouth, bazaar/marketplace), local currency in soʻm, no assumptions about tools that need a foreign card
- Include a "first 3 days" list — the smallest concrete actions to start immediately
- Length cap: under 700 words or one screen; no 10-section consultant report for a small business
- Ask for a critical pass at the end: "the weakest point of this plan and what would make it fail", 2–3 sentences
- Numbers the user did not give stay as [placeholders]; the prompt lists which numbers the user should fill in
- Two-stage output: a 3-sentence summary first, then the detailed table
## Avoid
- Plans without dates, numbers or an owner ("improve marketing", "work on quality")
- Inventing the user's revenue, prices or costs to make the plan look complete
- Long theory sections about why planning matters
- Recommending loans, hiring, agencies or paid tools when the user said the budget is small
- Mixing a business plan, a marketing plan and a content plan into one prompt — one plan, one horizon
