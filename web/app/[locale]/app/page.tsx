import { setRequestLocale } from "next-intl/server";
import { WorkbenchLoader } from "@/components/workbench-loader";

export default async function AppPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  return <WorkbenchLoader />;
}
