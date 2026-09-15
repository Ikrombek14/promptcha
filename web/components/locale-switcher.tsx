"use client";

import { useLocale, useTranslations } from "next-intl";
import { usePathname, useRouter } from "@/i18n/navigation";
import { locales, type Locale } from "@/i18n/routing";
import { cn } from "@/lib/utils";

export function LocaleSwitcher() {
  const t = useTranslations("locales");
  const locale = useLocale();
  const pathname = usePathname();
  const router = useRouter();

  return (
    <div
      role="group"
      className="flex h-10 items-center gap-1 rounded-[var(--radius)] border border-border bg-surface-2 p-1"
    >
      {locales.map((l: Locale) => (
        <button
          key={l}
          type="button"
          aria-pressed={l === locale}
          onClick={() => router.replace(pathname, { locale: l })}
          className={cn(
            "h-8 rounded-[var(--radius-sm)] px-2.5 text-label-md font-medium transition-colors",
            l === locale
              ? "border border-border bg-surface text-text"
              : "text-muted hover:text-text",
          )}
        >
          {t(l)}
        </button>
      ))}
    </div>
  );
}
