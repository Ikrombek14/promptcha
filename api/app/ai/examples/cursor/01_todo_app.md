## Input
Oddiy vazifalar ilovasi qilmoqchiman, telefonda ishlasin.
- users: faqat oʻzim
- features: qoʻshish, belgilash, oʻchirish

## Prompt
**Goal:** Build a simple personal to-do web app that works well on a phone, for a single user, no login.

**Stack:** Next.js 15 (App Router) + TypeScript + Tailwind CSS. Store tasks in the browser's localStorage (no backend, no database).

**Features (MVP):**
1. Add a task by typing text and pressing Enter or a button.
2. Mark a task done/undone with a tap; done tasks show strikethrough and move to the bottom.
3. Delete a task with a small delete button (confirm is not needed).
4. Tasks persist after page reload (localStorage).
5. Show an empty state message when there are no tasks.

**Data model:** Task { id: string, text: string, done: boolean, createdAt: number }.

**Pages / screens:** One page `/` with the input at the top and the list below.

**Constraints:** UI text in Uzbek (Latin script): "Yangi vazifa", "Qoʻshish", "Oʻchirish", "Hozircha vazifa yoʻq". Mobile-first layout, minimum tap target 44px, font size at least 16px. Keep everything in 2–3 files. No extra libraries.

**Steps:**
1. Scaffold the Next.js app with TypeScript and Tailwind.
2. Create the task list component with add / toggle / delete and localStorage sync.
3. Style for mobile, add the empty state.
4. Run it and tell me how to start it.

**Do not:**
- Do not add a database, auth, or state-management libraries.
- Do not use `any` in TypeScript.
- Do not skip the empty state or the persistence.

**Out of scope (for now):** categories, due dates, sync between devices.
