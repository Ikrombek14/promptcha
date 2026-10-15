Sen Promptcha (promptcha.uz) loyihasida ishlaysan. Loyiha papkasida `docs/promptcha-redesign/` bor — unda yangi dizayn, logo va ishlar rejasi.

1. Avval quyidagilarni toʻliq oʻqi:
   - `docs/promptcha-redesign/TASKS.md` — ishlar rejasi (A, B, C, D bosqichlar). Asosiy hujjat shu.
   - `docs/promptcha-redesign/README.md` — dizayn qoidalari.
   - `docs/promptcha-redesign/design/tokens.css` va `logo/` papkasi.
   - `docs/promptcha-redesign/design/reference-v2/` dagi ekranlar (`.dc.html` — stillar inline, `{{}}` shablon oʻzgaruvchisi, oxiridagi `<script>` holat mantiqi).
   README va TASKS.md zid boʻlsa, TASKS.md va reference-v2 ustun.

2. Keyin loyihani oʻrgan: stek, papka tuzilishi, generator sahifasi, prompt yaratish API'si, maʼlumotlar bazasi, i18n (Oʻz/Ru/En), admin panel, limit va token hisobi qayerda.

3. Menga **faqat A-bosqich uchun** reja yoz: qaysi fayllar oʻzgaradi, qaysilari yangi, qanday jadval va migratsiyalar, qanday yangi kutubxonalar kerak. Hech narsani oʻzgartirma — tasdiqlashimni kut.

Ish qoidalari:
- Har bosqich alohida branch'da: `redesign/a`, `feature/b-credits`, `feature/c-project-voice`. `main` ga toʻgʻridan-toʻgʻri push qilma.
- Bosqich ichida ham kichik qadamlar bilan ishla (A.1, A.2…), har qadamdan keyin nima qilinganini va qanday tekshirishni qisqa yoz.
- Mavjud funksiyalar buzilmasin: prompt yaratish, ball, anatomiya, tarix, Google login, admin panel, token hisobi.
- Yangi tashqi xizmat (toʻlov, ovozni matnga aylantirish) qoʻshishdan oldin menga ayt — kalitlarni men `.env` ga qoʻyaman. Hech qanday kalitni kodga yozma.
- Matnlar i18n orqali, oʻzbekcha apostrof doim `ʻ` (oʻ, gʻ).
- Kompyuterda 1366×768 ekranga sahifa skrollisiz sigʻsin, telefonda 360px dan boshlab ishlasin.
- Bosqich oxirida `TASKS.md` dagi "30 kunda isbot" metrikalarini oʻlchash uchun kerakli hodisalar yozilayotganini tekshir.
