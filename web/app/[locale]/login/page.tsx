import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { LoginCard } from "@/components/login-card";

type Params = Promise<{ locale: string }>;
type Search = Promise<{ error?: string; next?: string }>;

export async function generateMetadata({
  params,
}: {
  params: Params;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "auth" });
  return { title: t("title") };
}

export default async function LoginPage({
  params,
  searchParams,
}: {
  params: Params;
  searchParams: Search;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const { error, next } = await searchParams;
  return (
    <div className="flex flex-1 items-center justify-center px-4 py-8">
      <LoginCard error={error ?? null} next={next ?? null} />
    </div>
  );
}
