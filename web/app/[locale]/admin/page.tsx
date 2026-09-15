import { setRequestLocale } from "next-intl/server";
import { Overview } from "@/components/admin/overview";

export default async function AdminOverviewPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  return <Overview />;
}
