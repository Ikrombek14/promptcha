"use client";

// Admin qobigʻi: kirish tekshiruvi (useUser) + boʻlimlar navigatsiyasi.
// undefined → skeleton; null → /login; admin emas → /app; admin → nav + kontent.

import { useEffect } from "react";
import { useTranslations } from "next-intl";
import { MotionConfig } from "motion/react";
import { Link, usePathname, useRouter } from "@/i18n/navigation";
import { LOGIN_PATH, useUser } from "@/lib/auth";
import { Skeleton } from "@/components/ui/callout";
import { cn } from "@/lib/utils";

const SECTIONS = [
  { key: "overview", href: "/admin" },
  { key: "users", href: "/admin/users" },
  { key: "payments", href: "/admin/payments" },
  { key: "settings", href: "/admin/settings" },
] as const;

function ShellSkeleton() {
  return (
    <div className="mx-auto w-full max-w-[1100px] px-4 py-6 md:px-6" aria-busy>
      <Skeleton className="mb-6 h-9 w-72" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Skeleton className="h-28" />
        <Skeleton className="h-28" />
        <Skeleton className="h-28" />
        <Skeleton className="h-28" />
      </div>
      <Skeleton className="mt-6 h-64" />
    </div>
  );
}

export function AdminShell({ children }: { children: React.ReactNode }) {
  const t = useTranslations("admin");
  const user = useUser();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (user === null) router.replace(LOGIN_PATH);
    else if (user && !user.is_admin) router.replace("/app");
  }, [user, router]);

  if (!user || !user.is_admin) return <ShellSkeleton />;

  return (
    <MotionConfig reducedMotion="user">
      <div className="mx-auto w-full max-w-[1100px] px-4 py-6 md:px-6">
        <div className="mb-6 flex flex-wrap items-center gap-x-6 gap-y-3 border-b border-border pb-4">
          <span className="font-serif text-headline-md text-text">
            {t("title")}
          </span>
          <nav
            aria-label={t("nav.aria")}
            className="-mx-1 flex flex-wrap gap-2 overflow-x-auto px-1"
          >
            {SECTIONS.map((s) => {
              const active =
                s.href === "/admin"
                  ? pathname === "/admin"
                  : pathname.startsWith(s.href);
              return (
                <Link
                  key={s.key}
                  href={s.href}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "inline-flex h-9 items-center whitespace-nowrap rounded-[var(--radius-sm)] border px-3 text-label-md font-medium transition-colors duration-200 select-none",
                    active
                      ? "border-text bg-text text-bg"
                      : "border-border bg-surface-2 text-text hover:border-muted",
                  )}
                >
                  {t(`nav.${s.key}`)}
                </Link>
              );
            })}
          </nav>
        </div>
        {children}
      </div>
    </MotionConfig>
  );
}
