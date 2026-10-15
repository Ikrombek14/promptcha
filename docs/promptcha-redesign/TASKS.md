# Promptcha — ishlar rejasi

Claude Code uchun: bu faylni va `README.md` ni toʻliq oʻqi. Avval loyiha tuzilishini oʻrgan va **har bir bosqich uchun** qisqa reja yoz
(qaysi fayllar, qaysi jadvallar, qanday yangi kutubxonalar). Men tasdiqlaganimdan keyin boshlaysan. Har bosqichni alohida branch'da qil
va tugagach toʻxtab koʻrsat. Mavjud funksiyalar (prompt yaratish, ball, anatomiya, tarix, Google login, admin panel) buzilmasin.

**Yoʻnalish:** asosiy auditoriya — vibe coder'lar (Lovable/Cursor'da ilova quradiganlar). **Rasm uchun promptlar ham qoladi**
va hamma yangi funksiyalar (ball, "90+ ga yetkazish", kreditlar, ulashish, ovoz) ilova va rasm turlari uchun birdek ishlaydi.

**Dizayn namunalari:**
- `design/reference/` — v1: umumiy uslub, logo, natija paneli.
- `design/reference-v2/` — v2: shu rejadagi yangi funksiyalarning ekranlari (kompyuter 1366×768 ga skrollsiz sigʻadi, telefon 390×844).
- `logo/` — tayyor logo kodi, `design/tokens.css` — ranglar va oʻlchamlar.

| Bosqich | Nima | Taxminiy vaqt |
|---|---|---|
| A | Yangi dizayn + logo + kichik oʻzgarishlar + hodisalar yozuvi | 6–8 kun |
| B | "90+ ga yetkazish", kreditlar va toʻlov, toʻliq spek, ulashish | ~12 kun |
| C | "Loyiham" (loyiha pasporti) va ovoz bilan kiritish | ~6 kun |
| D | Keyinroq: rasm referensi, Telegram bot | — |

---

## A-bosqich — yangi dizayn va asos (6–8 kun)

### A.1 Hodisalarni yozib borish — 1 kun (BIRINCHI)
Yangi jadval `events`: `id, user_id (null boʻlishi mumkin), guest_id, session_id, name, payload (JSON), created_at`.

| name | payload |
|---|---|
| `idea_submitted` | gʻoya matni, tili (uz/ru/en), kiritish usuli (text/voice) |
| `type_detected` | tur, arxetip (logo, poster, MVP…) |
| `tool_selected` | vosita, avtomatikmi yoki foydalanuvchi tanladimi |
| `questions_answered` | savollar va javoblar |
| `prompt_generated` | prompt_id, versiya, umumiy ball, 6 mezon boʻyicha ballar, project_id (boʻlsa) |
| `prompt_copied`, `prompt_shared` | prompt_id |
| `limit_reached` | mehmon yoki kirgan |
| `prompt_feedback` | prompt_id, worked / not_worked, izoh |

- Yozish asosiy oqimni sekinlashtirmasin (fon rejimida, xato boʻlsa yutib yuborsin).
- Admin panelda oddiy voronka: kunma-kun gʻoya → prompt → nusxa → "ishladi", turlar boʻyicha.
- Foydalanish shartlariga: "Xizmatni yaxshilash uchun anonim foydalanish maʼlumotlari saqlanadi."

### A.2 Yangi dizayn va logo — 4–5 kun
`README.md` dagi koʻrsatmalar boʻyicha: tokenlar, Manrope + JetBrains Mono, matnli logo va uning 4 holati, generator sahifasi, natija paneli, prompt anatomiyasi, boʻsh / yuklanish / xato holatlari, mobil koʻrinish.
Kompyuterda 1366×768 ekranga **sahifa skrollisiz** sigʻsin (`design/reference-v2/V2-Home`, `V2-Result` namunalari).

### A.3 Bepul limit — 0.5 kun
- Mehmon: **2 ta** prompt. Kirgan foydalanuvchi: **kuniga 3 ta**. Qiymatlar env yoki admin panelda.
- Headerda: "Bugun N ta bepul qoldi" (3 ta nuqta bilan). Telefonda qisqa: "N bepul".
- Limit tugaganda: mehmonga "Google bilan kiring — kuniga 3 ta", kirganga "Ertaga yangilanadi" (B-bosqichdan keyin: "yoki kredit oling").

### A.4 "Prompt ishladimi?" — 1 kun
- Nusxa olingan prompt uchun foydalanuvchi **keyingi safar** kirganda natija panelining tepasida kartochka:
  "Kecha yozgan promptingiz ishladimi?" → [Ha, ishladi] [Yoʻq] [×]. "Yoʻq" bosilsa — ixtiyoriy bitta qator izoh.
- Har prompt uchun bir marta. Tarix sahifasida ham har prompt yonida shu tugmalar.
- Namuna: `V2-Home.dc.html`, `V2-M-Home.dc.html`.

### A.5 Birinchi ekranda 3 ta namuna — 0.5 kun
Bosilganda textarea toʻladi:
1. Ilova: "Oʻquv markazim uchun oʻquvchilar davomatini belgilaydigan oddiy web ilova"
2. Ilova: "Restoranim uchun Telegram orqali buyurtma qabul qiladigan sayt"
3. Rasm: "Yangi ochilgan qahvaxonam uchun Instagram'ga post rasmi, iliq ranglarda"

### A.6 Soddalashtirish — 0.5 kun
- Tarjima tugmasi → kichik havola "Tarjimasini koʻrish".
- Vosita: bitta tavsiya + "Oʻzgartirish" (ilova uchun standart Lovable).
- Kutubxona menyudan vaqtincha yashirilsin (kod oʻchirilmasin). Menyu: Generator, Tarix (C-bosqichda + Loyihalarim).

---

## B-bosqich — pul topish (~12 kun)

### B.1 "90+ ga yetkazish" — 2 kun
- Ball < 90 boʻlsa: eng past 2–3 mezon oddiy tilda ("Kayfiyat aniq emas", "Kamera burchagi yoʻq") va **asosiy tugma** "90+ ga yetkazish". Shu holatda chap paneldagi "Qayta yaratish" ikkinchi darajali tugmaga aylanadi.
- Bosilganda: kerak boʻlsa 1–2 savol → yangi versiya → yangi ball. Eski versiya tarixda.
- Narxi: 1 kredit. Kreditlar tayyor boʻlgunicha har foydalanuvchiga 3 ta bepul sinov.
- Namuna: `V2-Result.dc.html`, `V2-M-Result.dc.html`.
- **30 kunda isbot:** bali 80 dan past chiqqanlarning ≥35% bosadi.

### B.2 Kreditlar va Click/Payme — 4 kun
- Jadvallar: `credit_balance`, `credit_transactions` (miqdor ±, sabab, payment_id), `payments` (provayder, summa, holat, tashqi id).
- Paketlar (sozlamada): **15 000 soʻm → 40 kredit**, **35 000 soʻm → 120 kredit** ("Foydaliroq").
- Sarflanishi: "90+ ga yetkazish" 1, toʻliq spek 2, limitdan tashqari prompt 1, loyiha pasporti tahlili 1 (C.1).
- Click va Payme: callback imzosini tekshirish, idempotentlik (bitta toʻlov ikki marta hisoblanmasin), muvaffaqiyatsiz toʻlovda kredit qoʻshilmasin.
- Headerda kredit soni va "+" tugmasi; profilda tranzaksiyalar tarixi. Kreditlar muddatsiz. **Oylik obuna yoʻq.**
- Namuna: `V2-Paywall.dc.html`, `V2-M-Paywall.dc.html`.
- **30 kunda isbot:** faol kirgan foydalanuvchilarning ≥3% toʻlaydi.

### B.3 Ilova uchun toʻliq spek — 4 kun
- "Natija hajmi": [Tez prompt · bepul] [Toʻliq spek · 2 kredit].
- Boʻlimlar: Maqsad, Rollar, Sahifalar, Maʼlumotlar, Oqimlar, Dizayn, Qilinmasin. Har boʻlim ostida oʻzbekcha "nega kerak".
- MVP/UI playbook'lari asosida, 2–3 aniqlashtiruvchi savol bilan. Natija — bitta xabarda nusxalanadigan matn ("Lovable uchun nusxa olish").
- Namuna: `V2-Spec.dc.html`.
- **30 kunda isbot:** boshlangan speklarning ≥40% oxirigacha yetadi.

### B.4 Ommaviy ulashish sahifasi — 2 kun
- `/p/{qisqa_id}`: gʻoya (foydalanuvchi yashira oladi), prompt, ball va 6 mezon, anatomiya, "Oʻz gʻoyamni yozish" tugmasi.
- Telegram uchun OG rasm (gʻoya + ball). Rasm va ilova promptlari uchun.
- Namuna: `V2-Share.dc.html`, `V2-M-Share.dc.html`.
- **30 kunda isbot:** yangi roʻyxatdan oʻtishlarning ≥15% ulashilgan havoladan.

---

## C-bosqich — vibe coder uchun "Loyiham" va ovoz (~6 kun)

### C.1 "Loyiham" — loyiha pasporti — 3–4 kun
**Gʻoya:** kodni biz oʻqimaymiz (qimmat va ishonch kerak). Foydalanuvchining oʻz vositasi (Cursor, Lovable, Claude Code) loyihani oʻqib qisqa "pasport" yozadi,
foydalanuvchi uni Promptcha'ga qoʻyadi, va shundan keyin barcha promptlar shu loyihani hisobga olib yoziladi.

**Jadval** `projects`: `id, user_id, name, tool (lovable/cursor/claude_code/other), passport_raw (text), passport (JSON), created_at, updated_at`.

**Oqim:**
1. Menyuda "Loyihalarim". "Loyiha qoʻshish" → nom kiritiladi.
2. **1-qadam:** Promptcha quyidagi tayyor promptni koʻrsatadi, "Nusxa olish" tugmasi bilan, va oʻzbekcha izoh: "Buni Cursor / Lovable / Claude Code'ga yuboring. Kodingiz bizga yuborilmaydi."
3. **2-qadam:** foydalanuvchi chiqqan javobni maydonga qoʻyadi (maks. 10 000 belgi).
4. Promptcha uni JSON ga ajratadi (`what, stack, pages, data, done, in_progress, conventions`) va **oʻzbekcha qisqa xulosa** koʻrsatadi: "Loyihangiz: … · Tayyor: … · Chala: …" → [Toʻgʻri, saqlash] [Tahrirlash].
5. "Ilova" turida gʻoya maydoni ustida tanlov: "Loyiha: [Yoʻq ▾ / Davomat ilovasi ▾]". Loyiha tanlansa, generatsiyaga pasport qoʻshiladi va prompt
   mavjud narsalarni qayta qurmaslik, mavjud stek va tuzilmaga moslashish haqida aniq koʻrsatma bilan yoziladi.
6. Loyiha sahifasida: pasport xulosasi, shu loyiha uchun yozilgan promptlar tarixi va **"Keyingi qadam" — 3 ta taklif** (pasportdagi "chala" va "tayyor" asosida), bosilsa gʻoya maydoni toʻladi.
7. "Pasportni yangilash" — oʻsha promptni yana beradi, yangi javob eskisini almashtiradi (eski versiya saqlanadi).

**Pasport prompti (foydalanuvchi oʻz vositasiga yuboradi, aynan shu matn):**
```
Read this entire project and write a PROJECT PASSPORT in English, at most 600 words, using exactly these sections:
1. What it is — one sentence: what the app does and for whom.
2. Stack — language, frameworks, database, auth, hosting, key libraries.
3. Pages — every page or screen with its route and a one-line purpose.
4. Data — tables or collections with main fields and relations.
5. Done — features that work now.
6. In progress — half-done features, TODOs and known bugs.
7. Conventions — folder structure, naming, styling approach, state management.
Do not include secrets, API keys, passwords or .env values. Do not change any files.
```

**Narx:** bepul foydalanuvchiga 1 ta loyiha; pasportni tahlil qilish 1 kredit (birinchisi bepul). Loyihaga bogʻlangan oddiy prompt — odatdagidek.
**Xavfsizlik:** saqlashdan oldin pasport matnida kalitga oʻxshash qatorlarni (`sk-`, `AKIA`, `password=`, uzun base64 va h.k.) tekshirib, topilsa ogohlantirish va olib tashlash.
**Hodisalar:** `project_created`, `project_passport_saved`, `project_prompt_generated`, `project_next_step_clicked`.
**30 kunda isbot:** "Ilova" turidan foydalanganlarning ≥30% loyiha yaratadi va ularning ≥40% shu loyiha bilan 2+ prompt yozadi.
Bu natija chiqsa — keyin GitHub'dagi **ochiq** repolarni toʻgʻridan-toʻgʻri oʻqish (D-bosqich) haqida gaplashamiz.

### C.2 Ovoz bilan kiritish — 2–3 kun
**Gʻoya:** foydalanuvchi gʻoyasini oʻzbekcha, ruscha yoki inglizcha **aytadi**, matn gʻoya maydoniga tushadi, u tuzatib keyin yaratadi.

**Interfeys:**
- Kompyuter: textarea pastida tugma "Ovoz bilan aytish" (mikrofon ikonkasi).
- Telefon: textarea ichida oʻng pastda katta (44px+) mikrofon tugmasi.
- Bosilganda yozuv boshlanadi: qizil emas, oddiy holat — taymer (0:12 / 1:00), ovoz darajasi chizigʻi, [Toʻxtatish] va [Bekor qilish].
- Maksimum **60 soniya**, keyin avtomatik toʻxtaydi.
- Toʻxtatilgach: "Matnga aylantirilmoqda…" → matn textarea'ga qoʻshiladi (borini oʻchirmaydi), kursor oxirida. **Avtomatik yaratilmaydi** — foydalanuvchi tekshirib, oʻzi bosadi.

**Texnik:**
- Brauzerda `MediaRecorder` (Chrome/Android: webm/opus, Safari/iOS: mp4/aac) → backend `/api/transcribe` (multipart).
- Matnga aylantirish provayderi oʻzbek tilini qoʻllashi shart. **Provayderni oʻzing tanlama:** 2 ta variantni (masalan, OpenAI transkripsiya modeli va Google Speech-to-Text `uz-UZ`) sozlab,
  admin panelda sinov sahifasi qil — men 10 ta haqiqiy yozuv (oʻzbekcha, ruscha, aralash) bilan sinab, sifatini solishtirib tanlayman. Provayder env orqali almashadi.
- Natijada apostroflarni `ʻ` ga keltir (oʻ, gʻ), ortiqcha boʻshliqlarni tozala.
- Audio **saqlanmaydi**: matnga aylangach darhol oʻchiriladi.
- Limit: bepul foydalanuvchiga kuniga 10 ta ovozli kiritish, mehmonga 2 ta. Taxminiy xarajat: 30 soniya ≈ $0.003–0.006 — bitta prompt bilan teng.

**Xatolar (oʻzbekcha, aniq):**
- Mikrofonga ruxsat berilmagan → "Mikrofonga ruxsat bering: manzil qatoridagi qulf belgisi → Mikrofon → Ruxsat".
- Ovoz eshitilmadi → "Ovoz eshitilmadi. Yaqinroq gapirib, qayta urinib koʻring."
- Internet / server xatosi → "Matnga aylantirib boʻlmadi" + [Qayta urinish]; yozuv yoʻqolmasin.
- Brauzer qoʻllamasa → tugma yashiriladi.

**Hodisalar:** `voice_started`, `voice_transcribed` (davomiylik, til), `voice_failed` (sabab). `idea_submitted` da `input: voice`.
**30 kunda isbot:** telefondagi gʻoyalarning ≥15% ovoz bilan kiritiladi.

---

## D-bosqich — keyinroq

- **Rasm referensi → prompt** (5–6 kun): rasm yuklanadi → uslubni qayta yaratadigan prompt; "meni shu sahnaga qoʻy" — vositaga oʻz suratini ham yuklash haqida koʻrsatma bilan. Har biri 1 kredit. Rasm saqlanmaydi.
- **GitHub ochiq repo oʻqish** — faqat C.1 isbotlansa.
- **Telegram bot** — A–C koʻrsatkichlari yaxshi boʻlsa.
- **Open-source Claude Code skill / MCP** — qilinmaydi (playbook'lar asosiy boylik).

---

## Asosiy maqsad
Toʻlov ishga tushganidan keyin 60 kun ichida **30 ta foydalanuvchi ikkinchi marta toʻlasin.**
Shuning uchun A.1 (hodisalar) birinchi: oʻlchay olmagan narsamizni yaxshilay olmaymiz.
