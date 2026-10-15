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
  const t = await getTranslations({ locale, namespace: "pages.library" });
  return {
    title: t("title"),
    description: t("subtitle"),
    robots: { index: false, follow: false },
  };
}

// Kutubxona: faqat saqlangan promptlar.
export default async function LibraryPage({ params }: { params: Params }) {
  const { locale } = await params;
  setRequestLocale(locale);
  return <PromptList mode="library" />;
}
