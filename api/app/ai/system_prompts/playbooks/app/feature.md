# Feature: add functionality, fix a bug, refactor existing code
## Required facts
- change: what exactly must be added, fixed or improved, in one sentence | ask: What exactly should be added or fixed? | default: narrow the user's text to one change; if it is several, pick the first and list the rest as "later"
- current_behaviour: what happens now (the bug's symptom, the missing piece) and what should happen after | ask: What happens now, and what should happen instead? | default: [hozirgi holat] → [kutilgan holat]; for bugs, ask for the exact error message or steps to reproduce
- stack: the project's language, framework, database and where the relevant code lives (file/module names if known) | ask: Which stack/framework is the project, and where is the related code? | default: "detect from the repository and state it before changing anything"
- constraints: what must not change (public API, database schema, existing tests, design, dependencies) | ask: Anything that must stay unchanged — API, database, design? | default: no new dependencies, no schema change, existing tests keep passing
- acceptance: how the user will check it is done (a test, a screen, a command output) | ask: How will you check it works? | default: an automated test for the change plus a manual check described in one line
- scope: whether related cleanup is allowed | ask: Only this change, or is nearby cleanup okay? | default: only this change; note cleanup ideas separately
## Must include
- Goal line: the one change and who benefits
- Current vs expected behaviour, with exact error text or reproduction steps for bugs (or [xato matni] if the user has not pasted it)
- Pointers: files, functions, routes or screens involved; if unknown, an instruction to locate them first and report before editing
- Constraints list: do-not-touch areas, no new packages, backwards compatibility, UI language
- Acceptance criteria: 2–4 checkable statements ("the form shows 'Telefon raqam notoʻgʻri' for 8-digit input", "existing tests pass")
- Steps: read/locate → explain the cause or plan in 3 lines → implement → add or update a test → run tests → summarise the diff
- Rule to stop and ask if the cause is unclear or if the fix requires changing something in the constraints list
## Quality rules
- One change per prompt; a bug fix and a new feature never share a prompt
- Bugs: require root-cause explanation before the fix, and a regression test that fails before and passes after
- Refactors: behaviour must be identical — require "no functional changes, tests unchanged and green", and a size cap (e.g. touch at most 5 files)
- Minimal diff rule: no reformatting of untouched code, no renaming beyond the task, no drive-by upgrades
- Ask for a short summary at the end: what changed, which files, how to verify — 5 lines max
- Error and edge cases named explicitly (empty input, network failure, wrong language characters like ʻ in Uzbek)
- Keep the user's business facts and UI strings exactly; new UI text in the project's language and existing i18n mechanism
- Length: 120–300 words
## Avoid
- "Fix everything and make it better" without the concrete symptom and expected result
- Letting the agent rewrite the architecture to fix a small bug
- Adding libraries, migrations or config changes the user did not allow
- Guessing the stack or file names — locate first, then change
- Skipping the test because "it's a small change"
