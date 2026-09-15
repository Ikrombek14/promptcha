import type { Metadata } from "next";
import { Inter, Instrument_Serif, JetBrains_Mono } from "next/font/google";
import { NextIntlClientProvider, hasLocale } from "next-intl";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { notFound } from "next/navigation";
import Script from "next/script";
import { routing } from "@/i18n/routing";
import { SiteHeader } from "@/components/site-header";
import "../globals.css";

const instrumentSerif = Instrument_Serif({
  weight: "400",
  style: ["normal", "italic"],
  subsets: ["latin"],
  variable: "--font-instrument-serif",
  display: "swap",
});
const inter = Inter({
  subsets: ["latin", "cyrillic"],
  variable: "--font-inter",
  display: "swap",
});
const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin", "cyrillic"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});

// Tema flash'ini oldini oladi: birinchi chizishdan oldin data-theme oʻrnatiladi.
// ?theme=light|dark — havola bilan temani majburlash (skrinshot/tekshiruv uchun ham).
const themeScript = `(function(){try{var q=new URLSearchParams(location.search).get("theme");var t=(q==="dark"||q==="light")?q:localStorage.getItem("promptcha_theme");if(t!=="dark"&&t!=="light"){t=matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"}document.documentElement.setAttribute("data-theme",t)}catch(e){}})();`;

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "meta" });
  return {
    title: { default: t("title"), template: "%s · Promptcha" },
    description: t("description"),
    alternates: {
      languages: Object.fromEntries(routing.locales.map((l) => [l, `/${l}`])),
    },
  };
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!hasLocale(routing.locales, locale)) notFound();
  setRequestLocale(locale);

  return (
    <html
      lang={locale}
      suppressHydrationWarning
      className={`${instrumentSerif.variable} ${inter.variable} ${jetbrainsMono.variable} h-full`}
    >
      <head>
        <Script id="promptcha-theme" strategy="beforeInteractive">
          {themeScript}
        </Script>
      </head>
      <body className="flex h-full flex-col bg-bg text-text">
        <NextIntlClientProvider>
          <a
            href="#main"
            className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-[var(--radius-sm)] focus:bg-surface focus:px-3 focus:py-2"
          >
            {locale === "ru" ? "К содержимому" : locale === "en" ? "Skip to content" : "Asosiy qismga oʻtish"}
          </a>
          <SiteHeader />
          <main id="main" className="flex min-h-0 flex-1 flex-col">
            {children}
          </main>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
