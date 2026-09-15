import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { LocaleSwitcher } from "@/components/locale-switcher";
import { ThemeToggle } from "@/components/theme-toggle";
import { UserMenu } from "@/components/user-menu";

export function SiteHeader() {
  const t = useTranslations("header");
  return (
    <header className="border-b border-border">
      <div className="mx-auto flex h-14 max-w-[1312px] items-center justify-between px-4 md:px-6">
        <Link href="/app" className="font-serif text-headline-md text-text">
          {t("brand")}
        </Link>
        <div className="flex items-center gap-3">
          <LocaleSwitcher />
          <span className="hidden h-6 w-px bg-border sm:block" aria-hidden />
          <ThemeToggle label={t("theme")} />
          <UserMenu />
        </div>
      </div>
    </header>
  );
}
