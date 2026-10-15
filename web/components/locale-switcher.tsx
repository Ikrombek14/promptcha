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
      className="flex items-center gap-0.5 rounded-[var(--radius-md)] border border-border bg-surface-2 p-[3px]"
    >
      {locales.map((l: Locale) => (
        <button
          key={l}
          type="button"
          aria-pressed={l === locale}
          onClick={() => router.replace(pathname, { locale: l })}
          className={cn(
            "h-8 min-w-10 rounded-[7px] px-2.5 text-[13px] font-bold transition-colors",
            l === locale
              ? "bg-border-strong text-text"
              : "text-muted hover:text-text",
          )}
        >
          {t(l)}
        </button>
      ))}
    </div>
  );
}
