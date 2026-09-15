# Promptcha — CLAUDE.md

Oddiy so'zdan tayyor AI prompt yasaydigan platforma. Auditoriya: O'zbekistondagi boshlovchilar, biznes egalari, o'quvchilar. Domen: promptcha.uz.

## Stack

**Backend (`api/`)** — Python 3.12, FastAPI, uvicorn
- SQLAlchemy 2.0 async + asyncpg, Alembic
- AI provayderlar zanjiri (`AI_PROVIDERS=gemini,groq,mistral,openrouter`, `ai/llm.py`): kvota tugasa keyingisiga oʻtadi. Gemini — `google-genai`; Groq/Mistral/OpenRouter/custom — `openai` SDK (OpenAI-mos `/v1/chat/completions`); Anthropic — `anthropic` SDK (kalit kelganda zanjirga qoʻshiladi). Streaming — SSE orqali `sse-starlette`
- authlib (Google OAuth 2.0) + python-jose (JWT, httpOnly cookie). Faqat Google, parol yo'q
- slowapi (rate limit), pydantic-settings (`.env`)
- pytest + httpx (test)

**Frontend (`web/`)** — Next.js 15 App Router, React 19, TypeScript
- Tailwind CSS v4 (CSS-first `@theme`), shadcn/ui, lucide-react
- motion — maqsadli animatsiyalar: natija paneli chizigʻi, bosqich koʻrsatkichi, AI vositasi «ochilish» momenti (layoutId morph), izoh/savol stagger. Faqat transform/opacity, ≤300 ms (ochilish momenti 1.1 s — atayin), `useReducedMotion` hurmat qilinadi. Ambient loop'lar CSS keyframes (`globals.css`). Variantlar `lib/motion.ts` da
- next-intl — `/uz`, `/ru`, `/en`; default `uz`
- next/font — Instrument Serif, Inter, JetBrains Mono

**Infra** — PostgreSQL 16 (shu VPS), Nginx + Certbot, systemd (PM2 emas), Cloudflare DNS. Docker yo'q, Redis yo'q.

## Papka tuzilishi

```
promptcha/
  api/
    app/
      main.py            FastAPI app, CORS, routerlar
      config.py          Settings (pydantic-settings)
      db.py              engine, session
      models.py          User, UserContext, Prompt, UsageLog
      schemas.py         Pydantic in/out
      routers/
        auth.py          /api/auth/google, /api/auth/google/callback, /api/auth/me, /api/auth/logout
        prompts.py       /api/prompts (CRUD), /api/prompts/generate (SSE)
      ai/
        pipeline.py      classify → clarify → generate → explain
        system_prompts/  chatgpt.md, claude.md, midjourney.md, dalle.md, sora.md, cursor.md
        examples/        har AI uchun 5-10 ta namuna (input → prompt)
    alembic/
    tests/
    .env.example
  web/
    app/[locale]/
      page.tsx                    landing
      app/page.tsx                asosiy vosita
      login/page.tsx
      prompts/page.tsx
      prompts/[id]/page.tsx
      p/[slug]/page.tsx           public share
      pricing/page.tsx
      settings/page.tsx
    components/
      steps/                      Step1Input, Step2Type, Step3Ai, Step4Clarify, Step5Result
      ui/                         shadcn
    lib/api.ts                    fetch wrapper, SSE reader
    messages/uz.json, ru.json, en.json
  deploy/
    nginx.conf
    promptcha-api.service
    promptcha-web.service
  design/
    README.md                   qaysi fayl qaysi sahifa (indeks)
    landing/                    PNG/PDF/Figma eksport
    app/                        asosiy vosita — 5 qadam, holatlar
    login/
    prompts/
    settings/
    tokens.md                   ranglar, shriftlar, spacing — dizayndan olingan aniq qiymatlar
  docs/
    design-prompt.md            dastlabki dizayn talablari (dizayn fayllari ustun)
  CLAUDE.md
```

## Asosiy oqim (`/api/prompts/generate`)

1. `classify` — so'zdan turni taxmin qil (rasm/ilova/dizayn/video/matn), ishonch < 0.7 bo'lsa foydalanuvchidan so'ra
2. `clarify` — 1–2 ta aniqlashtiruvchi savol (chip variantlar bilan), qisqa
3. `generate` — `system_prompts/{ai}.md` + `examples/{ai}/` asosida prompt yasa, **stream** qilib qaytar
4. `explain` — 2–4 ta bir qatorlik izoh ("nega shunday")

Har bir qadam alohida funksiya, alohida test. AI mantiqi faqat `ai/` ichida — routerlar AI chaqirmaydi.

**Asosiy maqsad:** eng to'g'ri va sifatli promptni yozib berish. Prompt yasashdan oldin foydalanuvchining maqsadi aniq bo'lishi shart. Agar aniq bo'lmasa — savol beriladi, taxmin qilinmaydi. Tez javob emas, to'g'ri javob ustun.

## Xotira

**1. Tarix (`Prompt` jadvali)** — har bir yasalgan prompt saqlanadi: kirish matni, tur, tanlangan AI, aniqlashtiruvchi savol-javoblar, natija, izohlar, til, sana.
- Kirmagan foydalanuvchi: 3 ta bepul urinish, natijalar `localStorage`'da (`promptcha_guest`)
- Kirganda: guest promptlar bazaga ko'chiriladi, keyin `localStorage` tozalanadi
- Kirgan foydalanuvchi: har generate avtomatik saqlanadi, alohida "saqlash" tugmasi yo'q

**2. Kontekst (`UserContext` jadvali)** — foydalanuvchi haqida platforma o'rgangan doimiy faktlar: sohasi (masalan "restoran"), brend nomi, afzal uslubi, ko'p ishlatadigan AI.
- `clarify` va `generate` qadamlariga system prompt sifatida qo'shiladi
- Yangi fakt aniqlansa (foydalanuvchi "restoranim" dedi) — `UserContext`'ga yoziladi, keyingi safar so'ralmaydi
- Foydalanuvchi `/settings`'da ko'radi va o'chira oladi ("Platforma men haqimda nimani biladi")
- Guest foydalanuvchida kontekst saqlanmaydi

## Tillar

`uz` (default), `ru`, `en`. Til uch joyda ishlaydi:
- UI — `next-intl`, `messages/*.json`
- Savollar va izohlar — foydalanuvchi tilida (`pipeline`'ga `locale` uzatiladi)
- Natija prompt — **har doim ingliz tilida** (AI'lar inglizcha promptga yaxshi javob beradi), faqat foydalanuvchi "o'zbekcha bo'lsin" desa — tanlangan tilda

Til URL'da: `/uz/app`, `/ru/app`, `/en/app`. Brauzer tili bo'yicha birinchi kirishda taklif, keyin `settings`'da o'zgaradi.

`system_prompts/*.md` — loyihaning asosiy qiymati. Kod o'zgarmaydi, shu fayllar yaxshilanadi. Har birida: o'sha AI'ning uslub qoidalari, parametrlari (masalan Midjourney `--ar`, `--v`), nima qilish/qilmaslik, chiqish formati.

## Qoidalar

**Umumiy**
- Kichik qadamlar. Bitta vazifa = bitta PR o'lchamidagi o'zgarish
- Fayl yaratishdan oldin mavjudini tekshir
- Sirlar faqat `.env`'da. `.env` git'ga kirmaydi, `.env.example` yangilanadi
- O'zgarish qilganda mos testni yangilat yoki yoz

**Backend**
- Hamma DB ishi async. Sync chaqiruv yo'q
- Har bir router faqat HTTP bilan ishlaydi; mantiq `ai/` yoki servis funksiyalarda
- Xatolar: `HTTPException` + o'zbekcha `detail` (foydalanuvchi ko'radi)
- Rate limit: bepul — kuniga 5 generate, Pro — cheksiz. Hisob `usage_log`'da
- AI chaqiruvlarida (har qanday provayder) `max_tokens` ≤ 1500, `temperature` 0.4

**Frontend**
- Server Components default; `"use client"` faqat kerak joyda (steps, SSE reader)
- Shrift 16px'dan kichik bo'lmasin
- Bitta ekranda bitta primary tugma
- Har bir ro'yxat: empty / loading (skeleton) / error holati
- Matnlar faqat `messages/*.json` orqali, template ichida hardcode yo'q
- O'zbek matnida ʻ apostrof (oʻ, gʻ), ' emas

## Dizayn — MAJBURIY tartib

Tayyor UI/UX dizaynlar `design/` papkasida. **Har qanday frontend ishidan oldin:**

1. `design/README.md`'ni o'qi — qaysi fayl qaysi sahifaga tegishli
2. Yasalayotgan sahifaning dizayn faylini och va ko'r (PNG/PDF — `view` bilan, Figma eksport bo'lsa avval PNG'ga aylantir)
3. `design/tokens.md`'ni o'qi. Agar hali yo'q bo'lsa — dizayndan ranglar, shriftlar, o'lchamlar, spacing'ni ajratib olib **avval shu faylni yoz**, keyin kod yoz
4. Dizaynda ko'rsatilgan har bir holatni (empty, loading, error, hover, selected) topib, hammasini qur. Dizaynda yo'q holatni o'zing o'ylab top, lekin uslubdan chiqma
5. Sahifa tayyor bo'lgach dizayn bilan yonma-yon solishtir: joylashuv, o'lcham, rang, matn. Farq bo'lsa — kodni dizaynga moslashtir, aksincha emas

**Ustunlik tartibi:** `design/` fayllari > `design/tokens.md` > `docs/design-prompt.md` > quyidagi qisqa qoidalar. Dizayn faylida bor narsa — o'sha to'g'ri. Dizaynda yo'q narsa uchun quyidagiga amal qil.

Dizayn faylini ko'rmasdan UI yozish — taqiqlangan. Fayl topilmasa — to'xta va so'ra.

### Zaxira qoidalar (dizaynda ko'rsatilmagan holatlar uchun)

Uslub: sokin, muharrirlik, qog'oz-va-siyoh. AI mahsuloti ko'rinmasin: gradient, glow, binafsha, sparkle ikonka — yo'q.

```
bg #F7F6F2 · surface #FFFFFF · border #E4E2DC
text #17181C · muted #6B6E76
accent #1D4ED8 (faqat primary tugma, tanlangan holat, focus)
dark: bg #121317 · surface #1A1B20 · border #2A2C33 · text #ECECEA
```

Shrift: sarlavha Instrument Serif, matn Inter 16, prompt JetBrains Mono 15.
Radius 10px, 1px border (soya yo'q), 4/8px spacing, max-width 640px (vosita), 1100px (landing).
AI brendlari — faqat 8px nuqta chipda.

Agar `design/tokens.md`'dagi qiymatlar yuqoridagidan farq qilsa — tokens.md to'g'ri.

## Deploy — jonli holat (2026-09-15)

**Server:** Robbit yangi serveri `root@169.58.130.201` (SSH kalit sozlangan). Repo: `Ikrombek14/promptcha` (private).

| Nima | Qayerda |
|---|---|
| Kod | `/opt/promptcha/app` (foydalanuvchi `promptcha`, deploy key bilan clone) |
| API | systemd `promptcha-api`, port **8010** (8000 band — xonadosh), `.env` → `/opt/promptcha/app/api/.env` (600) |
| Web | systemd `promptcha-web`, port **3010** |
| Baza | tizim Postgres `127.0.0.1:5432`, baza/rol `promptcha`; parol `/root/.promptcha_pg` |
| TLS/domen | Caddy (`coach-caddy-1`), blok `/opt/coach/deploy/Caddyfile` → `deploy/robbit/Caddyfile.promptcha`; `X-Internal-Key` = `/root/.promptcha_internal` |
| Zaxira | `/opt/promptcha/backups/pre-migrate-*.sql.gz` (har deploy'da migratsiyadan oldin, 30 ta) |
| Loglar | `journalctl -u promptcha-api -n 50 --no-pager` |

**Deploy = `git push origin main`.** `.github/workflows/deploy.yml` (robbit-quiz uslubi, testsiz): ssh → `scripts/ci-deploy.sh <sha>` (zaxira → `uv sync` → `alembic upgrade head` → `npm ci && npm run build` → systemd restart) → `/api/health` dagi `commit` push qilingan sha bilan solishtiriladi, mos kelmasa yiqiladi. Secrets: `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY`. Heredoc tuzogʻi: skript `ssh -n` bilan argument sifatida chaqiriladi, STDIN orqali emas. Serverga `scp` bilan fayl tashlanmaydi.

Boshqa (Nginx'li) server uchun umumiy yoʻriqnoma: `deploy/README.md`. Deploy'dan oldin lokalda: `uv run pytest`, `npm run lint && npm test`, `.env.example` yangi, migratsiya bor.

**Jonli:** https://promptcha.uz (2026-09-15 dan; DNS A → 169.58.130.201, proxysiz; `www` → 301). Caddy Docker tarmogʻida (172.18.0.0/16) turgani uchun ufw'da `8010/tcp` va `3010/tcp` faqat `172.18.0.0/16` ga ochilgan (boshqa loyihalar bilan bir xil tartib) — bu qoidasiz Caddy 502 beradi. Jonli tekshiruv: `/api/health` 200, `/api/docs` 403, sarlavhasiz `POST /api/prompts/analyze` 403, brauzer oqimi (tahlil → savol → prompt) ishlaydi; tahlil serverda ~1,2 s.

### Xavfsizlik modeli (2026-09-15)

- API va Next faqat `127.0.0.1`; tashqaridan faqat Nginx 443.
- `app/security.py` (sof ASGI middleware, SSE'ga xalaqit bermaydi): `/api/*` uchun (1) `X-Internal-Key` = `INTERNAL_API_KEY` (Nginx qoʻshadi; prod'da majburiy, dev'da boʻsh → tekshirilmaydi), (2) `X-Requested-With: promptcha` (frontend `lib/api.ts` har fetch'ga qoʻshadi), (3) `Origin`/`Referer` faqat `CORS_ORIGINS`/`FRONTEND_URL` (POST'da majburiy), (4) tana ≤ 64 KB, (5) `no-store`, `nosniff`, `DENY`, `no-referrer` sarlavhalari. `/api/health` ochiq. Rad javobi 403 oʻzbekcha.
- Limitlar serverda: daqiqalik slowapi (real IP: `TRUST_PROXY=true` boʻlsa `X-Forwarded-For`), guest jami `GUEST_TOTAL_GENERATIONS` va IP kuniga `GUEST_DAILY_IP_GENERATIONS` — `usage_log` (faqat muvaffaqiyatli generate yoziladi, `ip` ustuni migratsiya 0002). Baza ishlamasa 503 (fail-closed).
- `APP_ENV=production` da `Settings.production_problems()` zaif sirlar/sozlamalar bilan serverni ishga tushirmaydi (APP_SECRET, JWT_SECRET, INTERNAL_API_KEY ≥ 32, TRUST_PROXY, https, localhost yoʻq, DB paroli).
- Prod'da `/api/docs`, `/api/openapi.json` yoʻq (FastAPI ham, Nginx ham). Next: `poweredByHeader: false`, xavfsizlik sarlavhalari, rewrites faqat dev'da.
- Dev'da port 8000 «arvoh» soket bilan band boʻlib qolgani uchun API 8001 da, `web/.env.local` → `API_URL=http://127.0.0.1:8001` (git'da yoʻq).

## Qabul qilingan qarorlar (2026-09-14)

- **Next.js 16** (create-next-app shuni beradi; 15 eskirgan). Farqlar: `middleware.ts` → `proxy.ts`, `params` async. Dev'da `/api/*` → FastAPI `next.config.ts` rewrites orqali (prod'da Nginx).
- **Tezlik (2026-09-15):** zanjirda **Groq birinchi** (`AI_PROVIDERS=groq,gemini,...`) — Gemini 3.7 tez-tez 503 berib SDK ichida sekin qayta urinardi (tahlil 16 s). Gemini klientida `HttpRetryOptions(attempts=2)`, tahlil (`classify`) natijasi 15 daqiqa xotirada keshlanadi (matn boʻyicha), frontend tahlilni 8 s dan ortiq kutmaydi (mashhur uchlik bilan davom etadi). Natija: tahlil ~1 s.
- **Provayder qatlami** `ai/llm.py`: pipeline faqat `llm.parse(system, user, Schema)` va `llm.stream(system, user)` ni biladi. Zanjir: `AI_PROVIDERS` tartibida, kaliti yoʻqlar tashlab ketiladi, 429/5xx → keyingi provayder; har provayder ichida `*_FALLBACK_MODELS`. OpenAI-mos provayderlarda structured output = `response_format=json_object` + sxema system promptda + pydantic tekshiruv (400 boʻlsa `response_format`siz qayta). Tekin tariflar (2026-09): Groq 30/daqiqa, 6k token/daqiqa (sinalgan, ishlaydi); Mistral Experiment ~1 mlrd token/oy; OpenRouter 50/kun; Gemini har model ~20/kun. Registrda yana: sambanova, huggingface, hyperbolic, cerebras, cohere (github.com/OuterSpacee/free-ai-apis roʻyxatidan; kalit qoʻyilsa ishlaydi, model nomi `/v1/models` bilan tekshiriladi). Cerebras va GitHub Models tekin tarifni yopgan. Rasm/video generatsiya kerak boʻlsa: Pollinations (auth yoʻq), Hugging Face, Replicate ($5). Gemini 2.5 yangi foydalanuvchilarga yopiq — `gemini-3.7-flash`. Gemini 3.x'da `thinking_budget=0` 400 beradi, `thinking_level=low` ishlatiladi (`GEMINI_THINKING_LEVEL`). Bepul tarif: har model kuniga ~20 soʻrov (bitta oqim = 3–4 soʻrov), shuning uchun `GEMINI_FALLBACK_MODELS` — 429/503 boʻlsa keyingi model sinaladi. Ishlab chiqarishda pullik kalit kerak. Umumiy limitlar: `AI_MAX_TOKENS=1500`, `AI_TEMPERATURE=0.4`.
- **anthropic SDK 1.x**: `temperature` imzodan olib tashlangan — `extra_body={"temperature": 0.4}` orqali, faqat 4.6/4.5 modellar uchun (`ai/client.py`). Model boshqa oilaga o'zgarsa temperature avtomatik tushib qoladi.
- Structured output: `client.messages.parse(output_format=PydanticModel)` (classify/clarify/explain). Generate — `messages.stream`.
- SSE hodisalari: `classify`, `clarify`, `delta`, `explain`, `done{status: ok|needs_kind|needs_clarification}`, `error`. Aniqlashtirish kerak bo'lsa oqim `done` bilan to'xtaydi, frontend javoblar bilan qayta chaqiradi.
- **Generate = job** (`services/jobs.py`, xotirada, Redis yo'q): `POST /generate → {job_id}`, `GET /jobs/{id}` SSE (avval replay, keyin jonli), `POST /jobs/{id}/cancel`. Ish brauzerdan mustaqil yuradi. Frontend butun vosita holatini `localStorage("promptcha_draft")`da saqlaydi; sahifa yangilansa yoki til almashsa holat tiklanadi va yasalayotgan ishga qayta ulanadi. Shu sabab Workbench `next/dynamic` `ssr:false` bilan chiziladi (hydration farqi bo'lmasin). Tugagan ish 15 daqiqa saqlanadi.
- **Bir ekran (2026-09-15, egasi qarori):** `/app` desktopda skrollsiz bitta ekranga sigʻadi (body `h-full`, ikki ustun ichida skroll). Dizayndagi header tagline, sarlavha osti izoh, "Maslahat", "Standart tekshiruv" callout, pastki meta qatori va footer olib tashlangan — ortiqcha matn kerak emas. Footer keyinroq qaytishi mumkin.
- **AI katalogi va tavsiya (2026-09-15, egasi qarori):** 22 ta vosita `ai/catalog.py`da (ChatGPT GPT-6 Astra, Claude Fable 5.1, Gemini 3.8 Flash, Grok 4.6, DeepSeek V4-Pro, Perplexity, Salom AI, Midjourney v7, Flux, Ideogram, Adobe Firefly, Higgsfield, Veo 3.1, Kling 3.0, Seedance 2.0, Runway Gen-4.5, Pika, HeyGen, Canva AI, Gamma, ElevenLabs, Cursor/Claude Code). Sora olib tashlangan. Foydalanuvchiga toʻliq roʻyxat koʻrsatilmaydi: `POST /api/prompts/analyze` (yozib toʻxtagach) tur + **2–3 ta eng mos va mashhur vosita** qaytaradi, birinchisi tanlangan; "AI VOSITASI" yorligʻi va "Avto" chipi yoʻq. Prompt uslubi **oilalar** boʻyicha: `system_prompts/{chat,image,video,code,search,design,slides,voice,avatar}.md` + `notes/<tool>.md` izohi; maxsus fayli borlar (`midjourney.md`, `claude.md`) oʻzinikini oladi. Namunalar `examples/<tool>/` → `examples/<family>/`. `Classification.tools` (1–3), `classify` hodisasida `tools` ham keladi. Frontend `AI_META` katalog bilan bir xil boʻlishi shart.
- **Oqim oʻrtasida uzilish:** provayder matn chiqa boshlagach 503/429 bersa `llm.MidStreamError` → pipeline `reset` hodisasi beradi va generate'ni bir marta qaytadan boshlaydi; frontend promptni tozalaydi.
- Yo'nalish chiplari: dizayndagi 4 ta (Rasm, Ilova, Dizayn, Ssenariy) o'rniga pipeline'dagi 5 ta tur (Rasm, Ilova, Dizayn, Video, Matn) + "Avto" (classify). Uslub dizayndagidek.
- Dizayndagi "Holat simulyatsiyasi" tugmalari — dizayn vositasi, kodga kirmaydi. Holatlar real oqimdan keladi.
- Tema: `data-theme` + `localStorage("promptcha_theme")`, `useSyncExternalStore` (React 19 lint: effect ichida setState taqiqlangan).
- Guest: `localStorage("promptcha_guest")` = `{id, prompts[]}`; `guest_id` generate so'roviga yuboriladi (keyin usage_log uchun).
- shadcn CLI ishlatilmadi; `components/ui/` shadcn uslubida qo'lda (cva + tailwind-merge).

## Hozirgi holat

- [x] Repo, papkalar, `.env.example`
- [x] Modellar + birinchi migratsiya (`alembic upgrade head` lokal bazada hali tekshirilmagan — parol kerak)
- [x] `/api/prompts/generate` SSE bilan (auth'siz, test uchun) — 14 test o'tadi, haqiqiy API kalit bilan hali sinalmagan
- [x] `design/` papkasini o'rganish, `design/tokens.md` yozish
- [x] Step1–Step5 komponentlar (dizayn asosida) — `/[locale]/app` ishlaydi, build o'tadi
- [ ] Google auth (authlib) + guest → user ko'chirish
- [ ] Tarix sahifasi
- [ ] UserContext — kontekst xotirasi va settings'da ko'rsatish
- [ ] uz/ru/en — UI matnlari va pipeline'ga locale
- [ ] Landing
- [x] Deploy — https://promptcha.uz jonli, 169.58.130.201, GitHub Actions (`git push origin main`)

Bajarilganini `[x]` qil. Yangi qaror qabul qilinsa — shu faylga yoz.
