import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Payments } from "@/components/admin/payments";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "admin" });
  return { title: `${t("nav.payments")} — ${t("title")}` };
}

export default async function AdminPaymentsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  return <Payments />;
}
