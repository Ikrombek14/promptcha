import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { PromptList } from "@/components/pages/prompt-list";

type Params = Promise<{ locale: string }>;

export async function generateMetadata({
  params,
}: {
  params: Params;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "pages.history" });
  return {
    title: t("title"),
    description: t("subtitle"),
    robots: { index: false, follow: false },
  };
}

// Tarix: foydalanuvchining barcha yasagan promptlari (eng yangisi yuqorida).
export default async function HistoryPage({ params }: { params: Params }) {
  const { locale } = await params;
  setRequestLocale(locale);
  return <PromptList mode="history" />;
}
