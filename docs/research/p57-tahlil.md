# Protokol 57 (app.p57.uz) — raqobatchi tahlili

Sana: 2026-09-16. Manba: egasining premium hisobi orqali koʻrilgan sahifalar (bosh sahifa, 57 protokol, 48 premium prompt, kurslar, 53 AI tool). Bu hujjat — bizning kuzatuv va xulosalarimiz; ularning matnlari koʻchirilmagan va koʻchirilmaydi (oferta + mualliflik huquqi). Xom sahifalar faqat lokal vaqtinchalik papkada, repoda yoʻq.

## 1. Mahsulot qisqacha

- **Model:** bir martalik 379 000 soʻm, umrbod kirish, 3 kunlik qaytarish kafolati. Referal: doʻstga 10% chegirma, taklif qilganga +1 bepul baholash (≤5). Premium Telegram kanal.
- **Toʻrt boʻlim:** Protokollar (57 qoida), Kurslar (3 ta), Promptlar (48 shablon), AI toollar (53 ta, ovoz berish bilan).
- **Oʻrganish mexanikasi:** har protokol bitta sahifa — «Muammo (foydalanuvchi tilida shikoyat) → Nega bunday boʻladi? → Yechim → Mashq (oʻz promptingni yoz, AI 0–100 baholaydi, 5 urinish, 70+ ball = oʻzlashtirildi) → Yomon misol / Yaxshi misol (nusxalash, ChatGPT'da sinash)». Bosh sahifada «Bugungi mashq», «Keyingi qadam», haftalik peshqadamlar (telefon raqami bilan), Telegram bot orqali kunlik eslatma.
- **Kurs formati:** «AI asoslari: 57 protokol» = 342 karta = 57 × 6 karta turi (Hook → Fill-Blank → Fix-Prompt → Mission → Scorecard → Quiz), ~2 soat, 10 dars bepul. Yana ikkita kurs: «Tanqidiy fikrlash» (8 modul, 113 dars) va «NotebookLM» (7 modul, 96 dars), 1-modul bepul.
- **Til:** toʻliq oʻzbek lotin. Foydalanuvchi oʻzi oʻrganadi va oʻzi prompt yozadi — bu **kurs**, vosita emas.

## 2. 57 protokol — mazmun (bizning guruhlashimiz)

Har biri bitta qoida: «promptga X ni qoʻsh». Mavzular boʻyicha:

| Mavzu | Protokollar | Qoida mohiyati |
|---|---|---|
| Hajm va format | 1, 2, 7, 12, 16, 23, 26, 32 | soʻz/paragraf soni, raqamli roʻyxat, jadval, javob shabloni («A \| B \| C»), maxsus belgilar bilan ajratish, avval qisqa xulosa |
| Auditoriya va soddalik | 3, 5, 28 | kim uchun, qaysi daraja, «10 yoshli bolaga tushuntirgandek» |
| Misol va dalil | 4, 6, 11, 36 | har fikrga real misol, statistika/manba, manba formati |
| Cheklovlar | 10, 24, 27, 49 | nima haqida gapirmaslik, vaqt/byudjet chegarasi, maqtov soʻzlarini taqiqlash, sunʼiy cheklov (kreativlik uchun) |
| Tanqidiy fikr | 13, 19, 25, 29, 31, 38, 40, 42 | eng kuchli qarshi argument, eng yomon holat, afzallik/kamchilik, rejaning zaif nuqtasi, yashirin taxminlar |
| Nuqtai nazarlar | 9, 14, 35, 37, 51 | ikki soha bilan tahlil, turli kasb vakillari roli, raqib koʻzi bilan, aloqasiz sohalarni birlashtirish |
| Sifat sikli | 18, 20, 30, 48, 56 | avval toʻliq keyin qisqartir, oʻz javobini tekshir, «2.0 versiya», iterativ yaxshilash, feedback loop |
| Biznes va reja | 21, 22, 33, 34, 39, 43, 44, 45, 46, 47, 50, 52, 53, 54, 55, 57 | qadam-baqadam, aniq muammo raqamlar bilan, foyda-xarajat/ROI, prioritet (80/20), 1 oy/1 yil/5 yil, 3 ssenariy (ehtimollik bilan), KPI, tizimli yondashuv, teskari rejalashtirish, MVP, SOP/checklist, A/B variantlar, 10x/avtomatlashtirish, Plan B |
| Model xulqi | 8, 15, 17, 41 | kreativlik darajasini soʻz bilan boshqarish, ishonch foizi, «maʼlumot yetarli emas» deyish, framework nomi (SWOT, SMART, 5W1H) |

Kuzatuvlar: qoidalar 2023–2024 «prompt engineering» maslahatlari; bir nechtasi takror (23≈26, 4≈36, 13≈40≈42, 30≈48). Baʼzilariga 2026 uchun izoh qoʻshilgan («reasoning modellar oʻzi tekshiradi», «AI agentlar», «internetdan qidir»). Misollar qisqa va kuchli: «Yomon: Sotuvni qanday oshirish mumkin? → Yaxshi: Oyiga 50 ta mijoz, oʻrtacha chek $30, 2 baravar oshirish uchun 5 ta aniq strategiya».

## 3. 48 premium prompt — tuzilma

Kategoriyalar: Biznes tahlili, Marketing, Gʻoya yaratish, Kontent yaratish, Dasturlash. Rasm/video/dizayn/ovoz yoʻq — faqat chat modellar uchun.

Har prompt aynan bir qolipda (300–600 soʻz, oʻzbekcha; sayt «inglizcha» deb yozgani bilan hammasi oʻzbekcha):
1. **Rol + tajriba** («15+ yillik», «CFO darajasida», «global brendlar bilan ishlagan»).
2. **Kirish maydonlari** — 4–6 ta `[KATTA_HARFLI_PLACEHOLDER]`: kompaniya, soha, auditoriya, maqsad, byudjet, muddat, hozirgi muammo.
3. **Buyruq** — «Keng qamrovli … tizimini ishlab chiqing».
4. **7–12 raqamlangan boʻlim**, har birida 4–6 band; ichki bosqichlar muddat bilan (0–90 kun / 3–6 oy / 6–12 oy), son talablari («5 ta persona», «10 ta slogan», «top 7 raqobatchi», «1–10 baho»), framework nomlari (SWOT, SCAMPER, TRIZ, RFM, Business Model Canvas, OWASP Top 10, Lean Six Sigma).
5. **Yakuniy qator** — chiqish tili/uslubi: «tushunarli oʻzbek tilida, amaliy misollar/aniq raqamlar/muddatlar bilan».

Baho: sifatli, lekin «konsultant hisoboti» uslubida — kichik biznes egasi uchun ortiqcha ogʻir (10 boʻlimli strategiya oʻrniga bitta post yoki taklif kerak). Placeholder'ni foydalanuvchi oʻzi toʻldiradi, noaniq boʻlsa ham savol yoʻq. Bizning oqim (tahlil → savol → prompt) aynan shu boʻshliqni yopadi.

## 4. AI toollar (53 ta)

Jamoa roʻyxati + ovoz. Eng koʻp ovoz: ChatGPT 32, Claude 26, Perplexity 10, Gemini 7, Tilmoch 5, DeepL 5. Tavsiflar eskirgan (GPT-4, Claude 100K kontekst, Runway Gen-2, DALL-E, Pika Discord orqali) — bizning 22 talik katalog (Fable 5.1, Gemini 3.8, Veo 3.1, Kling 3.0, Seedance 2.0) ancha dolzarb. Oʻzbek vositalari: Tilmoch, Kotib AI (bizda Salom AI). Bizda yoʻq, lekin ularda bor va foydali: NotebookLM, Suno/Udio (musiqa), Synthesia (bizda HeyGen), Photoroom/Remove.bg (mahsulot foto), Otter/Fireflies (transkript), n8n (avtomatlashtirish).

## 5. Promptcha uchun xulosalar

**Bizning ustunlik.** Dinamik oqim (sayt oʻzi tahlil qiladi, savol beradi, promptni yozadi), 22 vosita (rasm/video/ovoz/dizayn ham), inglizcha natija (modellar uchun sifatliroq), bepul boshlanish, dolzarb katalog. P57 — statik shablonlar + oʻqitish kursi; foydalanuvchi bilim olishi kerak, bizda esa bilim kerak emas.

**Qoidalar sifatida olish (oʻz soʻzlarimiz bilan).** Hozirgi `system_prompts/chat.md` (300 soʻz) allaqachon rol/vazifa/kontekst/talablar/format tuzilmasini beradi. Qoʻshish kerak boʻlgan aniq talablar:
1. **Sonlar** — har promptda kamida ikkita miqdor: uzunlik (soʻz/paragraf/band) va variantlar soni («3 ta sarlavha varianti»). (P57 #1, #2, #7, #54)
2. **Javob shabloni** — natija shakli aniq ustunlar/boʻlimlar bilan («Tushunish \| Kechirim \| Yechim \| Keyingi qadam»). (#16, #23, #26)
3. **Tanqid bandi** — biznes qarori/reja/gʻoya boʻlsa promptga «eng kuchli 3 qarshi argument», «eng yomon holat», «yashirin taxminlar» bandi majburiy. (#13, #19, #38, #40)
4. **Raqamli faktlar** — foydalanuvchi bergan sonlar (mijoz soni, chek, byudjet, muddat) promptda saqlanadi; bermagan boʻlsa clarify soʻraydi yoki `[…]` placeholder. (#22, #24)
5. **Framework nomi** — biznes/marketing/tahlil turida mos framework avtomatik qoʻshilsin (SWOT, SMART, AIDA, PAS, RFM, 5W1H, Business Model Canvas). (#41)
6. **KPI/oʻlchov** — strategiya/reja promptida «har tavsiya uchun KPI va oʻlchash usuli». (#44, #46)
7. **Prioritet** — roʻyxat kutilganda «muhimlik boʻyicha sarala / 80/20». (#34, #47)
8. **«Bilmasang ayt»** — faktik/yangilik savollarida «maʼlumot yetarli boʻlmasa taxmin qilma, shuni ayt» qatori. (#15, #17)
9. **Cheklovlar** — «nima haqida gapirma», «maqtov soʻzlarsiz» — kontent/tavsif promptlarida. (#10, #27)
10. **Ikki bosqichli natija** — uzun tahlil kutilganda «avval 3 gaplik xulosa, keyin batafsil». (#18, #32)

**Pipeline'ga:**
- `clarify`: tur boʻyicha majburiy faktlar roʻyxati — biznes matni: auditoriya + maqsad + ohang; marketing: kanal + byudjet/muddat; kontent: platforma + uzunlik; tahlil/qaror: hozirgi raqamlar + cheklov. Savollar shu boʻshliqlarga qarab tanlanadi.
- `explain` izohlari «qaysi qoida qoʻllandi»ni aytsa (masalan «Soʻz soni belgilandi — model hajmni taxmin qilmaydi») — foydalanuvchi oʻrganib ham boradi, P57'dagi oʻqitish qiymatini bepul beramiz.

**Mahsulot gʻoyalari (keyin, alohida qaror):**
- Prompt sifatini ball bilan baholash (0–100, 5 mezon) — bizda «Nega shunday?» bor; ball qoʻshish oson.
- Kunlik mashq / Telegram eslatma (retention).
- Referal chegirma (Pro chiqqanda).
- Boʻsh ekranda kategoriyali boshlangʻich gʻoyalar chip'lari («Instagram post», «Telegram eʼlon», «logotip», «taklif xati»).
- Katalogga qoʻshish nomzodlari: NotebookLM (tadqiqot), Suno (musiqa), Photoroom (mahsulot foto).
