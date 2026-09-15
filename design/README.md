# design/ — indeks

| Fayl | Sahifa | Izoh |
|---|---|---|
| `screen.png` | `/app` — asosiy vosita, **Natija** holati | Ikki ustun: chap — kirish kartasi (matn, yoʻnalish chiplari, AI chiplari, primary tugma, "Standart tekshiruv" callout); oʻng — natija paneli (prompt bloki, izohlar, aniqlashtirish savollari). Header (logo, til, tema, avatar), meta qatori (loyiha, faol rejim, holat simulyatsiyasi), footer. |
| `screen2.png` | — | `screen.png` bilan bir xil (nusxa) |
| `code.html` | `/app` | Stitch eksporti (Tailwind CDN). Faqat joylashuv va spacing uchun manba; class nomlari kodga koʻchirilmaydi. |
| `code2.html` | — | `code.html` nusxasi |
| `DESIGN.md` | dizayn tizimi | Matn qismi haqiqiy (ranglar, shrift, komponentlar). Frontmatter — Stitch avtomatik palitrasi, ishlatilmaydi. |
| `DESIGN2.md` | — | `DESIGN.md` nusxasi |
| `tokens.md` | hammasi | Kod uchun yagona haqiqat: ranglar, shriftlar, spacing, holatlar |

## Dizayni yoʻq sahifalar

Quyidagilar uchun dizayn fayli yoʻq — `tokens.md` va CLAUDE.md zaxira qoidalari asosida, `/app` uslubida quriladi:

- `/` landing
- `/login`
- `/prompts`, `/prompts/[id]`
- `/p/[slug]` public share
- `/pricing`
- `/settings`
- `/app` ning **Boʻsh**, **Yuklanmoqda**, **Xato** holatlari (dizaynda faqat tugmalar bor, ekran yoʻq) — `tokens.md` "Holatlar" jadvali
- `/app` aniqlashtirish savoli (Step4Clarify) — natija panelidagi savol kartalarini asos qilib chip variantlar bilan
