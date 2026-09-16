# General app / code task
## Required facts
- goal: what the code should do for whom, in one sentence | ask: What should it do, and for whom? | default: one sentence derived from the user's text; ask if unclear
- environment: the language/framework, or "new project" | ask: Which language/framework, or is it a new project? | default: new project with a beginner-friendly stack chosen and stated by the model
- acceptance: how success is checked | ask: How will you know it works? | default: a runnable example plus one automated test for the main path
## Must include
- Goal line and the stack or environment stated (chosen explicitly when the user did not specify)
- Concrete, numbered requirements (3–7), each testable
- Constraints: UI/text language, no unnecessary dependencies, secrets in `.env`, keep files small
- Steps in order, ending with "run it and tell me how to start / test it"
- A rule to ask before proceeding if a requirement is ambiguous
## Quality rules
- One deliverable per prompt (a script, a feature, a bot, a page) — not a whole platform
- No placeholders in code-critical parts (stack, entities, routes); [placeholders] only for business facts
- Error handling and empty/invalid input handled and named as requirements
- Tests or a verification command required for the main behaviour
- Local context stated when relevant: Uzbek/Russian text, phone-number contact, soʻm formatting, Telegram integration
- Length: 120–300 words, markdown sections
## Avoid
- Vague goals ("a modern app", "something like X") with no feature list
- Letting the agent decide scope, stack and data model silently
- Requesting deploy, payments and auth in the first version
- Several unrelated coding tasks in one prompt
