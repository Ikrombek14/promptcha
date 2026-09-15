import { redirect } from "@/i18n/navigation";

// Landing hali dizaynsiz — hozircha vositaga yoʻnaltiriladi.
export default async function Home({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  redirect({ href: "/app", locale });
}
