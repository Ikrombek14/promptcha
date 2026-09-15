## Input
Telegram bot kerak, mijozlar buyurtma qoldirsin, menga xabar kelsin.
- business: tort buyurtma
- language: oʻzbekcha

## Prompt
**Goal:** Build a Telegram bot that takes cake orders from customers step by step and forwards each order to the owner.

**Stack:** Python 3.12 + aiogram 3 + SQLite (via built-in `sqlite3`). Bot token and owner chat id in a `.env` file loaded with `python-dotenv`.

**Features (MVP):**
1. `/start` greets the customer in Uzbek and shows a "Buyurtma berish" button.
2. Order dialog (FSM): cake type (buttons: [tort turlari]), size in kg (buttons 1, 2, 3, other), delivery date (text), phone number (request contact button), optional note.
3. Confirmation message showing the full order with "Tasdiqlash" / "Bekor qilish" buttons.
4. On confirm: save the order to SQLite and send a formatted message to the owner's chat with the customer's Telegram username.
5. `/cancel` at any step cancels the dialog.

**Data model:** orders (id, tg_user_id, username, cake_type, size_kg, date, phone, note, created_at).

**Constraints:** All bot text in Uzbek (Latin script, use ʻ apostrophe). One process, long polling (no webhook). Handle a wrong input politely and repeat the question. Log errors to stdout.

**Steps:**
1. Create the project, `requirements.txt`, `.env.example`, and a `bot.py` with the FSM.
2. Add the SQLite helper and the owner notification.
3. Add input validation (phone, date) and `/cancel`.
4. Run it and tell me how to start it and where to put the token.

**Do not:**
- Do not add payments or an admin panel.
- Do not use a heavy ORM or Docker.
- Do not hardcode the token in code.

**Out of scope (for now):** order status updates, multiple owners, web dashboard.
