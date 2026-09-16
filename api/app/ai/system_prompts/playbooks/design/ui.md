# UI: screen or website mockup
## Required facts
- screen: which screen(s) to design and their purpose (a landing page for a course, an order form, an app home screen) | ask: Which screen is it, and what should the user do on it? | default: one screen from the user's text; if several, the first one, others as "later"
- users: who uses it, on which device, and the primary action | ask: Who uses it, on a phone or desktop, and what is the main action? | default: phone-first users in Uzbekistan; one primary action per screen
- content: the real text and elements (headline, sections, fields, buttons) in the audience's language | ask: What text and sections must be on the screen? | default: headline as [sarlavha], sections proposed by the model, all text in Uzbek (Latin)
- style: visual direction (clean minimal, bold, playful, corporate) and any brand colors | ask: What visual style, and do you have brand colors? | default: clean, light, one accent color, generous white space
- platform: web (desktop + mobile), mobile app (iOS/Android), Telegram mini app | ask: Web, mobile app or Telegram mini app? | default: responsive web, mobile-first
- states: which states matter (empty, loading, error, success, logged-out) | ask: Which states should be shown — empty, loading, error, success? | default: default + empty + error for every list or form
## Must include
- Screen name, purpose and the one primary action (one primary button per screen)
- Section order top to bottom with the exact content or [placeholders], in the audience's language
- Device frames and sizes: mobile 390×844, desktop 1440 wide; grid (4 columns mobile / 12 desktop), base spacing 8 px
- Typography: 1–2 fonts supporting Uzbek Latin and Cyrillic, minimum body size 16 px, heading scale (e.g. 32/24/20)
- Colors: background, surface, text, muted, one accent — named or hex placeholders; contrast at least 4.5:1
- Components list: buttons (primary/secondary), inputs with labels and error text, cards, navigation; touch targets at least 44 px
- States to draw: empty, loading (skeleton), error, success — for each list and form
## Quality rules
- One screen per prompt; a flow is 2–4 numbered screen prompts with a shared style line
- Copy is real or placeholder, never lorem ipsum; button labels are verbs in the UI language ("Buyurtma berish")
- Accessibility rules stated: contrast, focus states, labels on every input, no color-only meaning, text scalable
- Mobile-first: the phone layout described first; desktop as an adaptation
- Local patterns: phone number as the main identifier, Telegram/WhatsApp contact button, soʻm price formatting (120 000 soʻm), Uzbek and Russian language switch if needed
- Hierarchy rule: one headline, one primary action, max 3 secondary actions per screen
- For landing pages: section skeleton with counts (hero → 3 benefits → how it works in 3 steps → proof/testimonials as [placeholders] → price → FAQ 4–6 → CTA)
- Length: 150–300 words; structured brief with headings and lists
## Avoid
- "Modern, beautiful UI" with no sections, content, sizes or states
- Designing five screens in one prompt with no shared style line
- Decorative gradients, glow, mixed fonts and tiny text
- Inventing testimonials, prices, statistics for the mockup
- Skipping empty/error states so the developer has to guess
