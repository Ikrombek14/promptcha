import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";

type Params = Promise<{ locale: string }>;
type Section = { title: string; body: string[] };

export async function generateMetadata({
  params,
}: {
  params: Params;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "privacy" });
  return { title: t("title") };
}

// Maxfiylik siyosati va foydalanish shartlari — Google OAuth rozilik ekrani uchun ham talab qilinadi.
export default async function PrivacyPage({ params }: { params: Params }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations({ locale, namespace: "privacy" });
  const sections = t.raw("sections") as Section[];
  return (
    <div className="flex-1 overflow-y-auto px-4 py-8">
      <article className="mx-auto flex w-full max-w-[720px] flex-col gap-8">
        <header className="flex flex-col gap-2">
          <h1 className="font-serif text-headline-lg text-text">
            {t("title")}
          </h1>
          <p className="font-mono text-code-sm text-muted">{t("updated")}</p>
          <p className="text-body-md text-muted">{t("intro")}</p>
        </header>
        {sections.map((s) => (
          <section key={s.title} className="flex flex-col gap-3">
            <h2 className="font-serif text-headline-md text-text">{s.title}</h2>
            {s.body.map((p) => (
              <p key={p} className="text-body-md text-text">
                {p}
              </p>
            ))}
          </section>
        ))}
        <p className="text-body-md text-muted">{t("contact")}</p>
      </article>
    </div>
  );
}
