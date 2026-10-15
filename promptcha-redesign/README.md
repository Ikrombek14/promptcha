# Promptcha — yangi dizayn va logo (Claude Code uchun topshiriq)

Bu papka Promptcha (promptcha.uz) generator sahifasining yangi dizayni va yangi logosini oʻz ichiga oladi.
Vazifa: shu dizaynni **loyihaning mavjud stekida** (framework, komponentlar, stil usuli) joriy qilish.
Bu yerdagi HTML fayllar — namuna, ularni toʻgʻridan-toʻgʻri koʻchirma; loyihadagi tuzilmaga moslab qayta yoz.

## 0. Ishni boshlashdan oldin

1. Repo tuzilishini oʻrgan: qaysi framework, stil qanday yoziladi (Tailwind / CSS modules / oddiy CSS), generator sahifasi qayerda, i18n (Oʻz / Ru / En) qanday ishlaydi, model va "yoʻnalish" roʻyxatlari qayerda saqlanadi.
2. Menga qisqa reja yoz: qaysi fayllarni oʻzgartirasan, nimani yangidan yaratasan. **Tasdiqlaganimdan keyin** boshlaysan.
3. Yangi branch'da ishla: `redesign/v2`. Mavjud funksionallik (API chaqiruvlari, prompt yaratish, nusxa olish, tarjima) buzilmasin.

## 1. Papkada nima bor

| Fayl | Nima |
|---|---|
| `design/tokens.css` | Ranglar, radiuslar, shriftlar, harakat egri chiziqlari. Loyiha tema tizimiga koʻchir. |
| `logo/logo.html`, `logo/logo.css`, `logo/logo.js` | Yangi logo va uning animatsiyalari. **Aynan shunday** ishlat, faqat komponentga oʻra. |
| `design/reference/Main.dc.html` | Desktop generator sahifasi (natija bilan). Asosiy namuna. |
| `design/reference/Mobile.dc.html` | Mobil koʻrinish (390 px). |
| `design/reference/Empty.dc.html` | Natija paneli — boʻsh holat. |
| `design/reference/Loading.dc.html` | Natija paneli — yaratilmoqda holati. |
| `design/reference/Logo.dc.html` | Logo varagʻi: oʻlchamlar, yorugʻ fon, favicon. |
| `motion/*.html` | Logo animatsiyalarining jonli demo sahifalari (brauzerda ochib koʻrish mumkin). |

`.dc.html` fayllar haqida: barcha stillar inline `style="…"` ichida. `{{nom}}` — shablon oʻzgaruvchisi, `<sc-for>` — sikl, `<sc-if>` — shart. Oxiridagi `<script>` ichida `renderVals()` holat mantiqini koʻrsatadi (qaysi tur tanlanganda qaysi modellar chiqishi va hokazo). Bularni loyihangdagi komponent mantiqiga oʻgir.

## 2. Logo (birinchi navbatda)

- Logo — oddiy matn: **"Prompt"** `#EDEEF2` + **"cha"** `#8C93A4`, Manrope 800, `letter-spacing: -0.04em`. Hech qanday belgi, ikonka yoki gradient yoʻq.
- `Logo` komponenti yarat: `logo.html` dagi markup + `logo.css`. Oʻlcham `font-size` orqali (header 24px, mobil 22px).
- Holatlar (`logo.js` dagi `pcPlay`):
  - `is-intro` — bosh sahifa birinchi ochilganda, sessiyada bir marta (`pcIntroOnce`).
  - `is-loading` — "Promptni yaratish" bosilgandan keyin; javob 300 ms dan tez kelsa koʻrsatma.
  - `is-done` — natija kelgan zahoti bir marta.
  - `is-interactive` — header logosida hover (faqat sichqonchada).
- Favicon: faqat "P" harfi, `#171A22` fonda, `#EDEEF2`, Manrope 800 (16, 32, 180 px).
- Eski logo (koʻk kvadrat ichidagi "P" va serif "Promptcha") butunlay olib tashlansin.

## 3. Generator sahifasi (desktop) — `Main.dc.html`

**Header (64px, sticky, blur fon):** chapda logo; yonida navigatsiya "Generator / Kutubxona / Tarix" (aktiv sahifa pastki chiziq bilan, `aria-current="page"`); oʻngda til almashtirgich `Oʻz | Ру | En` (segment), tema tugmasi, avatar (rasm boʻlmasa ism initsiallari).

**Ikki ustun:** chapda kiritish (~40%), oʻngda natija (~60%). `flex-wrap` bilan, tor ekranda ustma-ust tushadi. Ichki skroll **yoʻq** — sahifaning oʻzi skroll qilinadi.

**Chap panel:**
1. Sarlavha "Fikringizni aniq promptga aylantiring" + izoh.
2. `<label>` "Gʻoyangiz" + hisoblagich `45 / 500`. Textarea pastida ikki tugma: "Ovoz bilan aytish" (mikrofon), "Gʻoyani boyitish". Agar loyihada bu funksiyalar boʻlmasa — tugmalarni qoʻyma yoki menga ayt.
3. **Natija turi** (fieldset, 3×2 grid, ikonkali): Avto, Rasm, Video, Ilova, Dizayn, Matn.
4. **Model** (2 ustunli karta: nom + versiya + qisqa izoh, tanlanganida koʻk ✓). **Muhim:** model roʻyxati tanlangan turga bogʻliq. Turi oʻzgarganda birinchi model avtomatik tanlanadi. Roʻyxatni loyihadagi haqiqiy modellardan ol; namunadagi nomlar (Kling, Lovable va h.k.) faqat misol.
5. **Nisbat** (faqat Rasm/Video uchun): 1:1, 4:5, 16:9, 9:16 — har birida kichik shakl ikonkasi. Tanlangan nisbat promptdagi `--ar` ga yoziladi.
6. Asosiy tugma (bitta!) "Promptni yaratish", yonida `Ctrl ↵` maslahati, 52px balandlik. Ostida ghost tugma "Boshidan boshlash".

**Tanlangan holat hamma joyda bir xil:** `background: rgba(58,99,240,.16); border-color: #4C7DFF`. Tanlanmagan: `#171A21` fon, `#262A35` chegara.

**Oʻng panel (natija):**
1. "Tayyor prompt" + model badge (`● Midjourney v7`) + **sifat halqasi**: 40px aylana progress (`#5FD3B5`), ichida ball, yonida "Aʼlo sifat / 100 balldan". Bu tugma emas — ramka bermang.
2. Segment "Inglizcha | Oʻzbekcha" (tarjima). Oʻzbekcha koʻrinishda izoh: "Tarjima faqat tushunish uchun. Modelga inglizcha variantni yuboring."
3. Oʻngda: "Kutubxonaga saqlash" (ikonka tugma) + "Nusxa olish" (oq fon, toʻq matn).
4. **Prompt bloki** (`#0E1015`, mono shrift 15px, line-height 1.85). Tepasida legenda: Obyekt / Kompozitsiya / Yorugʻlik va rang / Parametrlar. Promptning qismlari `tokens.css` dagi `.sg-*` klasslari bilan belgilanadi. Pastida: "65 soʻz · 412 belgi" va "Midjourney sintaksisi".
   - Agar backend prompt qismlarini alohida qaytarmasa: hozircha bitta rang bilan chiqar va menga qanday maydonlar kerakligini yoz (masalan `segments: [{type, text}]`).
5. **Prompt anatomiyasi**: 4 ta karta (rangli nuqta + nom, promptdan parcha, nega kerakligi). Bu eski "Muhandislik tahlili (sharhlar)" oʻrnini bosadi.
6. **Tez oʻzgartirish** chiplari: "+ Ertak uslubi", "+ Kinematografik", "+ Akvarel", "+ Iliqroq ranglar" — bosilganda prompt qayta yaratiladi (mavjud API imkon bersa).

## 4. Holatlar — `Empty.dc.html`, `Loading.dc.html`

- **Boʻsh:** ikonka, "Natija shu yerda paydo boʻladi", 3 ta namuna gʻoya (bosilganda textarea toʻladi), pastda klaviatura maslahatlari.
- **Yuklanish:** 3 bosqichli indikator (Gʻoya tahlil qilindi ✓ → Uslub tanlanmoqda ⟳ → Parametrlar), skeleton qatorlar, "Nusxa olish" disabled. Logo `is-loading`.
- **Xato:** nima boʻldi + "Qayta urinish" tugmasi (namunada yoʻq, loyiha uslubida qoʻsh).

## 5. Mobil — `Mobile.dc.html`

- Header 56px: logo, til, avatar.
- Gʻoya kartasi (matn + tanlangan tur/model/nisbat chiplari + "Tahrirlash").
- Natija kartasi, anatomiya roʻyxat koʻrinishida, gorizontal skroll qilinadigan "Tez oʻzgartirish".
- **Pastda doim koʻrinadigan panel:** "qayta yaratish" ikonka tugmasi + "Promptni nusxalash" (bosilganda 1.8 s "Nusxa olindi", yashil fon). `env(safe-area-inset-bottom)` ni hisobga ol.

## 6. Qoidalar

- Shriftlar: Manrope (400–800) + JetBrains Mono. Eski serif shriftni olib tashla.
- Oʻzbekcha apostrof: hamma joyda `ʻ` (U+02BB): "oʻ", "gʻ", "soʻz". Tirnoq `'` bilan aralashtirma.
- Ikonkalar: bitta kutubxona (Lucide tavsiya). Emoji yoʻq.
- Har bir interaktiv elementda `:focus-visible`, hover faqat `@media (hover:hover)` ichida, tegish maydoni ≥ 44px.
- `prefers-reduced-motion` hurmat qilinsin.
- Matnlar i18n tizimi orqali (Oʻz / Ru / En) — namunadagi oʻzbekcha matnlarni kalitlarga chiqar.

## 7. Tekshiruv (topshirishdan oldin)

- [ ] 360px, 768px, 1440px da tekshirildi, gorizontal skroll yoʻq
- [ ] Tur → model bogʻliqligi ishlaydi, nisbat promptga tushadi
- [ ] Nusxa olish, tarjima, qayta yaratish avvalgidek ishlaydi
- [ ] Logo 4 holati toʻgʻri joyda, intro sessiyada bir marta
- [ ] Klaviatura bilan butun sahifani boshqarish mumkin
- [ ] Eski logo va eski "Muhandislik tahlili" bloki qolmagan
