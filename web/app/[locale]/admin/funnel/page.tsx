import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Funnel } from "@/components/admin/funnel";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "admin" });
  return { title: `${t("nav.funnel")} — ${t("title")}` };
}

export default async function AdminFunnelPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  return <Funnel />;
}
