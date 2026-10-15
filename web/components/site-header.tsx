"use client";

import { useTranslations } from "next-intl";
import { Link, usePathname } from "@/i18n/navigation";
import { Logo } from "@/components/logo";
import { LocaleSwitcher } from "@/components/locale-switcher";
import { ThemeToggle } from "@/components/theme-toggle";
import { UserMenu } from "@/components/user-menu";
import { cn } from "@/lib/utils";

/** Header: 64px, yopishqoq, blur fon. Chapda logo + boʻlimlar, oʻngda til, tema, hisob. */
const NAV = [
  { href: "/app", key: "generator" },
  { href: "/library", key: "library" },
  { href: "/history", key: "history" },
] as const;

export function SiteHeader() {
  const t = useTranslations("header");
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-10 border-b border-border/70 bg-bg/85 backdrop-blur-xl">
      <div className="mx-auto flex min-h-16 max-w-[1280px] items-center gap-2 px-4 md:px-6 lg:gap-4 lg:px-8">
        <Link
          href="/app"
          aria-label="Promptcha"
          className="flex shrink-0 items-center rounded-[var(--radius-sm)] text-[22px] leading-none md:text-[24px]"
        >
          <Logo state="breathe" />
        </Link>

        <nav aria-label={t("nav")} className="hidden gap-1 md:flex lg:ml-2">
          {NAV.map(({ href, key }) => {
            const active = pathname === href || pathname.startsWith(`${href}/`);
            return (
              <Link
                key={href}
                href={href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "relative px-3 py-[21px] text-body-sm font-semibold transition-colors",
                  active
                    ? "text-text shadow-[inset_0_-2px_0_var(--selected-border)]"
                    : "text-muted hover:text-text",
                )}
              >
                {t(key)}
              </Link>
            );
          })}
        </nav>

        <div className="flex-1" />

        <div className="flex items-center gap-2">
          <LocaleSwitcher />
          <ThemeToggle label={t("theme")} />
          <UserMenu />
        </div>
      </div>
    </header>
  );
}
