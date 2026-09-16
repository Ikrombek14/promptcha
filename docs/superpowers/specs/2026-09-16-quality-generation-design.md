# Sifatli generatsiya — dizayn (2026-09-16)

Maqsad: prompt «umumiy yaxshi» emas, foydalanuvchining aniq holatiga qurilgan va tekshirilgan boʻlsin.
Chegara: LLM chaqiruvlar soni oshmaydi (3 ta: reja, prompt, tekshiruv), kutish vaqti uzaymaydi.
Manba: `docs/research/p57-tahlil.md` (57 protokol → 10 qoida) + vosita hujjatlari.

## Oqim (yangi)

```
yozib toʻxtadi → analyze: classify (kind, tools, archetype)  [kesh 15 min]
                    └─ fonda: plan (brif + savollar) → kesh          ← foydalanuvchi kutmaydi
«Prompt yasash» → job: plan keshdan (yoʻq boʻlsa 1 chaqiruv) → savol boʻlsa done{needs_clarification}
javoblar bilan → job: brif.facts += javoblar (LLM'siz) → generate (stream) → review (ball + izohlar)
```

Chaqiruvlar: reja (plan) 1, prompt (generate) 1, tekshiruv (review) 1 — hozirgi clarify/generate/explain oʻrniga, soni bir xil.

## 1. Playbook'lar — `api/app/ai/system_prompts/playbooks/<kind>/<archetype>.md`

Har vazifa arxetipi uchun bizning qoidalarimiz. Fayl formati (mashina oʻqiydi):

```md
# <Sarlavha>                       ← bitta qator
## Required facts
- <id>: <nima> | ask: <savol namunasi, foydalanuvchi tilida emas — inglizcha, model tarjima qiladi> | default: <boʻsh boʻlsa nima olinadi>
## Must include
- <prompt ichida albatta boʻlishi kerak bo'lgan element>
## Quality rules
- <arxetipga xos sifat qoidasi — sonlar, shablon, tanqid bandi, KPI, framework, cheklov...>
## Avoid
- <tipik xato>
```

Arxetiplar (kind → archetype):
- text: post, message, article, plan, analysis, script, learn, general
- image: logo, poster, product, portrait, scene, general
- video: ad, reel, story, talking, general
- app: mvp, feature, general
- design: brand, ui, slides, print, general

`general` har kind uchun majburiy (fallback). Classification `archetype` maydoni roʻyxatda boʻlmasa → `general`.

## 2. Sxemalar (`schemas.py`)

- `Classification` += `archetype: str = "general"`.
- `Brief`: goal, deliverable, audience, tone, answer_language, constraints: list[str], facts: dict[str,str] (foydalanuvchi bergan: nom, raqam, joy), missing: list[str] (playbook fact id'lari), success_criteria: list[str], framework: str = "", tool_params: dict[str,str].
- `PlanResult`: brief: Brief, questions: list[ClarifyQuestion] (≤2, faqat `missing` ichidan eng muhimlari; `id` = fact id).
- `ReviewResult`: score: int (0–100), criteria: list[{name, ok: bool, note}] (6 ta), notes: list[str] (2–4, «qaysi qoida — nega»).

## 3. Pipeline (`pipeline.py`)

- `classify` — system promptga arxetip roʻyxati va taʼrifi qoʻshiladi; `archetype` tozalanadi (kind roʻyxatida boʻlmasa general).
- `plan(text, kind, ai, locale, context) -> PlanResult` — system: playbook (Required facts + Must include), vosita nomi, brif taʼrifi, savol qoidalari (faqat missing, ≤2, koʻp tanlov uchun kombinatsiyalanadigan variantlar, foydalanuvchi tilida). Kesh: kalit (text, kind, ai, locale), 15 min, `_plan_cache`. `prefetch_plan(...)` — analyze'dan fonda chaqiriladi (asyncio task, meter bilan, xatoda jim).
- `apply_answers(brief, questions, answers) -> Brief` — LLM'siz: `answers[id]` → `facts[id]`, `missing` dan olib tashlanadi; «(not specified)» → default qoldi.
- `generate(...)` — system: family prompt + playbook (Must include, Quality rules, Avoid) + umumiy rubrika (6 mezon) + brif bloki (`<brief>` JSON) + FACTS RULE + examples. User: request + clarifications. Oʻzgarmas: stream, MidStream reset.
- `review(text, prompt, brief, ai, locale) -> ReviewResult` — explain oʻrniga; rubrika boʻyicha ball + izohlar. Izoh: «qoida — nega» (masalan «Soʻz soni belgilandi — model hajmni taxmin qilmaydi»).
- `run()` hodisalari: `classify{…, archetype}`, `clarify{questions}`, `delta`, `explain{notes, score, criteria}`, `done`. Yangi hodisa yoʻq — frontend mos.

Umumiy rubrika (6 mezon, generate va review'da bir xil): 1) aniq vazifa va natija turi; 2) foydalanuvchi faktlari saqlangan, yetishmagani `[…]`; 3) oʻlchanadigan talablar (uzunlik, soni, format); 4) auditoriya va ohang; 5) cheklovlar (nima qilmaslik); 6) umumiy gaplar/fillersiz, vosita sintaksisiga mos.

## 4. Router (`routers/prompts.py`)

- `/analyze`: classify'dan keyin `asyncio.create_task(pipeline.prefetch_plan(...))` (ai = tools[0]); javobga `archetype` qoʻshiladi.
- `/generate`: oʻzgarmas.

## 5. Frontend (2-bosqich)

- `explain` hodisasida `score`/`criteria` → Step5Result'da kichik ball belgisi (0–100) va izohlar.
- Ball < 75 → «Yaxshilash» tugmasi: `startGenerate` ga `improve: {previous_prompt, feedback}` → server generate'ni tanqid bilan qayta yozadi (plan/clarify oʻtkazib yuboriladi).

## 6. Eval (3-bosqich)

`api/evals/requests.jsonl` (20 real soʻrov, har kind), `api/evals/run.py`: eski (git tag) va yangi natijani yonma-yon, LLM-hakam balli + qoʻlda koʻrish. Natija jadvali egaga.

## Bosqichlar va fayllar

| Bosqich | Fayllar | Kim |
|---|---|---|
| 1a playbook matnlari | `system_prompts/playbooks/**` (25 fayl) | agent (kontent) |
| 1b pipeline | `schemas.py`, `ai/pipeline.py`, `ai/prompts.py` (playbook loader), `routers/prompts.py`, testlar | bosh sessiya |
| 2 ball + Yaxshilash | `pipeline.review`, `GenerateRequest.improve`, frontend Step5Result/workbench/api.ts | bosh sessiya |
| 3 eval | `api/evals/*` | bosh sessiya |

Har bosqich: testlar oʻtadi → commit → push (deploy) → jonli tekshiruv.
