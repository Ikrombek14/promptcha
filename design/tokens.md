# Promptcha — dizayn tokenlari

Manba: `design/DESIGN.md` (matn qismi) va `design/screen.png`. Bu fayl kod uchun yagona haqiqat.
`DESIGN.md` frontmatter'idagi Material-uslub ranglar (`#faf8fe`, `primary #0037b0` …) Stitch eksportining
avtomatik palitrasi — ular ishlatilmaydi. Faqat `error` rangi undan olingan.

## Ranglar

| Token | Light | Dark | Qayerda |
|---|---|---|---|
| `bg` | `#F7F6F2` | `#121317` | sahifa foni (qogʻoz) |
| `surface` | `#FFFFFF` | `#1A1B20` | kartalar, inputlar, menyular |
| `surface-2` | `#F7F6F2` | `#1F2026` | chip, callout, kod bloki foni, hover |
| `border` | `#E4E2DC` | `#2A2C33` | 1px chegaralar, ajratgichlar |
| `text` | `#17181C` | `#ECECEA` | asosiy matn |
| `muted` | `#6B6E76` | `#9A9DA6` | meta, placeholder, izoh |
| `accent` | `#1D4ED8` | `#3B82F6` | faqat: primary tugma, tanlangan holat, focus, 2px chap chiziq |
| `accent-soft` | `#EEF2FF` | `#1B2440` | tanlangan chip foni, prompt bloki highlight |
| `on-accent` | `#FFFFFF` | `#FFFFFF` | primary tugma matni |
| `error` | `#BA1A1A` | `#FF6B6B` | xato matni va chegarasi |
| `error-soft` | `#FFDAD6` | `#3A1F1F` | xato bloki foni |
| `scrim` | `rgba(23,24,28,.15)` | `rgba(0,0,0,.5)` | modal orqasi (blur yoʻq) |

Tanlangan yoʻnalish chipi (dizaynda "Rasm"): fon `text` (`#17181C`), matn `surface` (oq). Bu accent emas — ink.
Tanlangan AI chipi (dizaynda "Midjourney"): fon `surface`, chegara 1px `accent`, matn `text`.

AI brend nuqtalari (8px doira, faqat chipda):

| AI | Rang |
|---|---|
| Midjourney | `#1D4ED8` |
| ChatGPT | `#10A37F` |
| Claude | `#D97706` |
| DALL·E 3 | `#EC4899` |
| Cursor | `#17181C` |
| Sora | `#8B5CF6` |

## Shriftlar

`next/font`: Instrument Serif (400, italic bor), Inter (400, 500, 600), JetBrains Mono (400, 500).

| Token | Shrift | Oʻlcham / qator | Qayerda |
|---|---|---|---|
| `headline-xl` | Instrument Serif 400 | 44 / 52, `-0.02em` | landing hero |
| `headline-xl-mobile` | Instrument Serif 400 | 32 / 38, `-0.01em` | landing hero (mobil) |
| `headline-lg` | Instrument Serif 400 | 32 / 40, `-0.01em` | vosita sarlavhasi ("Fikringizni aniq promptga aylantiring") |
| `headline-md` | Instrument Serif 400 | 24 / 32 | natija paneli sarlavhasi ("Tayyor prompt"), logo |
| `headline-sm` | Instrument Serif 400 | 20 / 28 | boʻlim sarlavhalari |
| `body-lg` | Inter 400 | 18 / 28.8 | landing tavsif |
| `body-md` | Inter 400 | 16 / 25.6 | asosiy matn, textarea, izohlar (minimum) |
| `body-sm` | Inter 400 | 14 / 22.4 | faqat meta va yordamchi matn; asosiy matnga emas |
| `label-md` | Inter 500 | 14 / 20, `+0.01em` | tugma va chip matni |
| `label-sm` | Inter 500 | 12 / 16, `+0.02em`, uppercase | boʻlim yorliqlari ("YOʻNALISH", "AI VOSITASI") |
| `code-md` | JetBrains Mono 400 | 15 / 24 | tayyor prompt bloki |
| `code-sm` | JetBrains Mono 400 | 13 / 20 | meta (belgilar soni, "41 soʻz", versiya chipi, footer) |

Qoida: foydalanuvchi oʻqiydigan matn 16px'dan kichik boʻlmasin. `body-sm`, `label-sm`, `code-sm` faqat meta uchun.

## Radius

| Token | Qiymat | Qayerda |
|---|---|---|
| `radius` | 10px | karta, input, tugma, dialog, prompt bloki |
| `radius-sm` | 6px | chip, badge, versiya belgisi |
| `radius-xs` | 4px | kichik ichki elementlar |

Toʻliq dumaloq (`9999px`) taqiqlangan — faqat avatar va 8px brend nuqtasi.

## Chegaralar va chuqurlik

- Hamma ajratish 1px `border` bilan. Soya, blur, gradient, glow — yoʻq.
- Natija paneli: 1px `border` + chap tomonda 2px `accent` chiziq (dizaynda koʻrinadi).
- Izoh kartalari: `surface-2` fon, 1px `border`, chap 2px `accent`.
- Focus: input — chegara `accent` + 1px `accent` ring (halo yoʻq). Tugma — 2px `accent` outline, 2px offset.

## Spacing (4/8px toʻr)

| Token | px |
|---|---|
| `space-2xs` | 4 |
| `space-xs` | 8 |
| `space-sm` | 12 |
| `space-md` | 16 |
| `space-lg` | 24 |
| `space-xl` | 32 |
| `space-2xl` | 48 |
| `space-3xl` | 64 |

- Karta ichki padding: 24px (desktop), 16px (mobil).
- Chip ichki: 6px 12px. Chip orasidagi boʻshliq 8px.
- Boʻlimlar orasi (vositada): 24px. Yorliq va uning kontenti orasi: 8px.

## Oʻlchamlar va joylashuv

| Nima | Qiymat |
|---|---|
| Header balandligi | 80px, pastida 1px `border` |
| Kontent max-kengligi (vosita) | 1312px; ikki ustun 1fr / 1fr, orasi 24px |
| Bitta ustun (mobil/planshet < 1024px) | ustma-ust, natija paneli kirish kartasi ostida |
| Landing max-kengligi | 1100px |
| Bitta karta (vosita, tor rejim) | max 640px |
| Input balandligi | 40px; textarea min 180px |
| Primary tugma | balandlik 44px (dizaynda), toʻliq kenglik, matn chapda, klaviatura ishorasi oʻngda (`code-sm`) |
| Ikkilamchi tugma | 36px, `surface` fon, 1px `border` |
| Chip | 36px balandlik |
| Brend nuqtasi | 8px doira, matndan 8px chap |
| Footer | `surface-2` fon, yuqorida 1px `border`, 48px padding |

## Holatlar (dizayndagi "Holat simulyatsiyasi")

| Holat | Koʻrinishi |
|---|---|
| Boʻsh (`Boʻsh`) | Natija panelida markazda muted matn + qisqa yoʻriqnoma; panel chegarasi oddiy (accent chiziq yoʻq) |
| Yuklanmoqda (`Yuklanmoqda`) | 2–3 ta 64px balandlikdagi skeleton blok (`surface-2`, `animate-pulse`), prompt bloki matni stream boʻlib toʻladi |
| Natija (`Natija`) | Chap 2px accent chiziq, prompt bloki, izohlar, aniqlashtirish savollari |
| Xato (`Xato`) | `error-soft` fon, 1px `error` chegara, oʻzbekcha xabar + "Qayta urinish" ikkilamchi tugma |
| Hover (chip) | chegara `muted`ga oʻzgaradi, fon `surface-2` |
| Selected (chip) | yuqoridagi "tanlangan" qoidalar |
| Disabled (tugma) | 50% opacity, cursor not-allowed |

## Dark rejim

Header'dagi quyosh ikonkasi bilan almashadi; `data-theme="dark"` yoki `prefers-color-scheme`.
Dark qiymatlar jadvalda. Accent dark'da `#3B82F6` (kontrast uchun).
