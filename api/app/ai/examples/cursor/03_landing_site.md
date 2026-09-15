## Input
Stomatologiya klinikasi uchun sayt, bitta sahifa, qabulga yozilish formasi.
- style: toza, oq-koʻk
- lang: oʻzbek va rus

## Prompt
**Goal:** Build a single-page marketing website for a dental clinic with an appointment request form, in Uzbek and Russian.

**Stack:** Plain HTML + CSS + a little vanilla JavaScript. No framework, no build step. The form posts to a Telegram bot via a tiny Node.js (Express) endpoint in `server.js`; the bot token and chat id live in `.env`.

**Features (MVP):**
1. Sections: hero with a "Qabulga yozilish" button, services (6 cards), doctors (3 cards with placeholder photos), prices table, contact with map embed placeholder, footer.
2. Language switch UZ / RU in the header that swaps all text without reload (texts stored in a JS object).
3. Appointment form: name, phone, preferred date, service (select). On submit: validate, send to `/api/appointment`, show a success or error message.
4. Mobile-first responsive layout; sticky header on desktop.

**Data model:** none stored; each request is forwarded to Telegram.

**Pages / screens:** `index.html` only; `server.js` for the one API route.

**Constraints:** Clean white and blue design (#FFFFFF, #1D4ED8, light gray backgrounds), system fonts, no stock icons libraries. All text in a `texts` object with `uz` and `ru` keys; use placeholders like [Klinika nomi], [manzil], [telefon]. Phone validation for Uzbek numbers (+998).

**Steps:**
1. Create `index.html`, `styles.css`, `app.js` with the layout and language switch.
2. Add the form with validation and the fetch call.
3. Create `server.js`, `.env.example`, `package.json`; forward the form to Telegram.
4. Run it and tell me how to start it.

**Do not:**
- Do not add React, Tailwind, or a CSS framework.
- Do not store personal data anywhere.
- Do not skip the error state of the form.

**Out of scope (for now):** online payment, doctor schedules, admin panel.
