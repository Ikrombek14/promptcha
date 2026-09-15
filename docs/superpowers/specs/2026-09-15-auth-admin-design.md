# Auth + admin panel — dizayn (2026-09-15)

Egasi tasdiqlagan: Google login/logout, token hisobi, `/admin` shu sayt ichida, toʻlov hozircha qoʻlda,
kirgan bepul foydalanuvchiga kuniga 5 urinish. Admin: `ADMIN_EMAILS` roʻyxati (hozir `ikrombekmurodov7@gmail.com`).

## Boʻlaklar

1. **Auth** — Google OAuth, sessiya cookie, `/login`, chiqish, guest promptlarni koʻchirish.
2. **Token hisobi + admin** — har LLM chaqiruvi `llm_call` ga, `/admin` (Umumiy, Foydalanuvchilar, Toʻlovlar, Sozlamalar), limitlarni boshqarish, qoʻlda toʻlov.
3. **Onlayn toʻlov** (Payme/Click) — keyinroq; `payment.method` va `provider_ref` shunga tayyor.

## Maʼlumotlar modeli (migratsiya 0003)

- `users` +`pro_until` (timestamptz, null), +`bonus_generations` (int, default 0). `plan` mavjud (`free|pro`); Pro = `plan='pro'` va (`pro_until` null yoki kelajakda).
- `llm_call`: id, user_id?, guest_id?, job_id?, stage (`classify|clarify|generate|explain|facts`), provider, model, input_tokens, output_tokens, estimated (bool), ok (bool), duration_ms, created_at. Indekslar: created_at; (provider, created_at); (user_id, created_at).
- `payment`: id, user_id, amount (soʻm, int), currency (`UZS`), method (`manual|payme|click`), days (int), note?, provider_ref?, created_by (admin email), paid_at, created_at. Yozilganda `users.plan='pro'`, `pro_until = max(now, pro_until) + days`.
- `app_setting`: key (pk), value (text), updated_at. Kalitlar: `guest_total_generations`, `guest_daily_ip_generations`, `free_daily_generations`. Yoʻq boʻlsa `.env` qiymati. 60 s kesh, admin yozganda darhol yangilanadi.
- `usage_log`: mavjud; endi `user_id`, `input_tokens`, `output_tokens` ham toʻldiriladi.

## Backend

### services/auth.py (umumiy)
- JWT (python-jose, HS256, `JWT_SECRET`, `JWT_EXPIRE_DAYS`), cookie `promptcha_session` (httpOnly, Secure prod'da, SameSite=Lax, path `/`).
- `get_current_user` (ixtiyoriy, None qaytaradi), `require_user` (401), `require_admin` (403), `is_admin_email`.

### routers/auth.py (1-boʻlak)
- `GET /api/auth/google` → Google'ga (authlib, `state` cookie'da, `?next=/uz/app` faqat nisbiy yoʻl).
- `GET /api/auth/google/callback` → token almashish, `users` upsert (google_sub, email, name, avatar, last_login_at), cookie, `FRONTEND_URL + next` ga 302.
- `GET /api/auth/me` → `{id, email, name, avatar_url, plan, pro_until, is_admin, remaining_today, bonus_generations}` yoki 401.
- `POST /api/auth/logout` → cookie oʻchadi.
- `POST /api/auth/migrate` → guest promptlar roʻyxati (≤ 50) `prompts` ga yoziladi (dublikat: bir xil `result` va `input_text` bor boʻlsa oʻtkazib yuboriladi), `{saved}`.
- `GET /api/auth/dev-login?email=` — faqat `APP_ENV=development` va `AUTH_DEV_LOGIN=true`; prod'da `production_problems` rad etadi.
- SecurityMiddleware: `/api/auth/google`, `/api/auth/google/callback`, `/api/auth/dev-login` — brauzer navigatsiyasi, sarlavhalarsiz ochiq. Qolgan auth yoʻllari odatdagidek himoyalangan.

### Token hisobi (2-boʻlak)
- `ai/metering.py`: contextvar `Meter` — `new()`, `set_stage()`, `record(provider, model, in, out, estimated, ok, duration_ms)`.
- `ai/llm.py`: har provayder chaqiruvi `record` qiladi. OpenAI-mos stream: `stream_options={"include_usage": true}`; Gemini: `usage_metadata`; Anthropic: `message_start`/`message_delta`. Token kelmasa `len(text)//4`, `estimated=True`.
- `ai/pipeline.py`: `run` har bosqichda `set_stage`.
- `services/jobs.py`: `_run` boshida `Meter.new()`, oxirida (ok ham, xato ham) `usage.record_llm_calls(...)`; `done ok` da `record_usage(user_id, guest_id, ip, ai, tokens)`; kirgan foydalanuvchi uchun `Prompt` qatori saqlanadi (auto-save).
- `services/usage.py`: `check_quota(session, user, guest_id, ip)`: Pro → oʻtadi; kirgan free → bugungi `usage_log` soni < `free_daily_generations` yoki `bonus_generations > 0` (bonus muvaffaqiyatli generate'da 1 ga kamayadi); guest → hozirgi qoidalar. Limit qiymatlari `services/settings.py` dan.
- `routers/prompts.py`: `generate` `get_current_user` bilan; `user_id` job'ga.

### routers/admin.py (2-boʻlak, `require_admin`)
- `GET /api/admin/stats?days=7|30` → `{active_users: {today, d7, d30}, generations: {today, d7, d30}, tokens: {input, output}, by_tool[], by_provider[] (provider, model), by_stage[], top_users[] (email, generations, tokens), daily[] (date, generations, tokens)}`.
- `GET /api/admin/users?q=&page=&limit=` → sahifalangan roʻyxat (email, name, plan, pro_until, bonus_generations, generations_total, tokens_total, created_at, last_login_at).
- `POST /api/admin/users/{id}/grant` → `{plan?: free|pro, pro_days?: int, bonus_generations?: int (qoʻshiladi)}`.
- `GET /api/admin/payments?page=` va `POST /api/admin/payments` → `{user_id, amount, method, days, note}`; Pro uzayadi.
- `GET /api/admin/settings`, `PUT /api/admin/settings` → uchta limit.
- Har amal `log.info` bilan (kim, nima).

## Frontend

- `lib/auth.ts` (umumiy): `User` tipi, `fetchMe()`, `logout()`, `useUser()` (useSyncExternalStore; `null` = kirmagan, `undefined` = yuklanmoqda).
- `/[locale]/login`: `/app` uslubida karta — sarlavha, bitta Google tugmasi (`/api/auth/google?next=/{locale}/app`), izoh. Kirgan boʻlsa `/app` ga.
- Header avatar: kirmagan → `/login`; kirgan → menyu (email, plan, «Admin» (faqat admin), «Chiqish»).
- Kirgach `/app`: guest promptlar boʻlsa `POST /api/auth/migrate`, keyin `promptcha_guest.prompts` tozalanadi (id qoladi). Kirgan foydalanuvchida guest hisoblagich oʻrniga «Bugun: N ta qoldi» (`/me`dan), Pro'da koʻrsatilmaydi.
- `/[locale]/admin` (layout `useUser`: admin boʻlmasa `/app` ga): **Umumiy** (kartalar: faol foydalanuvchilar bugun/7/30, generatsiyalar, tokenlar; jadval: vosita, provayder/model, bosqich, top foydalanuvchilar; kunlik chiziq — oddiy CSS bar), **Foydalanuvchilar** (qidiruv, jadval, qator amallari: Pro berish (kun), bonus qoʻshish), **Toʻlovlar** (roʻyxat + «Qoʻlda qoʻshish» formasi), **Sozlamalar** (uchta limit).
- Matnlar: `messages/{uz,ru,en}.json` `auth` nomfazosi; admin matnlari alohida `messages/admin/{uz,ru,en}.json` (i18n `request.ts` birlashtiradi).
- Uslub: `design/tokens.md`, qogʻoz-siyoh, jadval + 1px chiziqlar, grafik kutubxonasi yoʻq, shrift ≥ 16px.

## Test
- Backend: `test_auth.py` (dev-login, me, logout, migrate, admin ruxsati, cookie parametrlari), `test_metering.py` (meter, token yigʻish, estimated), `test_usage.py` (free kunlik, bonus, pro, guest), `test_admin.py` (403 oddiy foydalanuvchiga, grant/payment mantiqi soxta sessiya bilan).
- Frontend: lint + tsc + build; brauzer skripti: dev-login → header menyu → admin sahifalari → logout.

## Parallel ish chegaralari
| Agent | Faqat shu fayllar |
|---|---|
| A auth-backend | `routers/auth.py`, `tests/test_auth.py` (+ `services/auth.py` kengaytirish) |
| B metering-backend | `ai/llm.py`, `ai/pipeline.py`, `ai/metering.py`, `services/jobs.py`, `services/usage.py`, `routers/prompts.py`, `tests/test_metering.py`, `tests/test_usage.py`, `tests/test_generate_route.py` |
| C admin-backend | `routers/admin.py`, `services/admin.py`, `tests/test_admin.py` |
| D auth-frontend | `app/[locale]/login/**`, `components/site-header.tsx`, `components/user-menu.tsx`, `components/workbench.tsx`, `lib/guest.ts`, `lib/auth.ts`, `messages/{uz,ru,en}.json` |
| E admin-frontend | `app/[locale]/admin/**`, `components/admin/**`, `lib/admin-api.ts`, `messages/admin/*.json` |

Umumiy poydevor (modellar, migratsiya, config, security, `services/auth.py`, `services/settings.py`, `ai/metering.py` interfeysi, `lib/auth.ts`, i18n birlashtirish, router stublari) — agentlardan oldin bosh sessiya yozadi.
