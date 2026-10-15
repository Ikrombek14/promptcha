"use client";

// Tarix/Kutubxona holatlari: yuklanish (skeleton kartalar), boʻsh, xato, kirmagan + sahifalash.
// Uslub: promptcha-redesign/design/reference (Empty.dc.html, Loading.dc.html).

import type { ReactNode } from "react";
import { useLocale, useTranslations } from "next-intl";
import { AlertTriangle, LogIn, RotateCcw } from "lucide-react";
import { Link } from "@/i18n/navigation";
import { Button, buttonVariants } from "@/components/ui/button";
import { googleLoginUrl } from "@/lib/auth";
import { cn } from "@/lib/utils";

/** Bitta kartaning skeleti — haqiqiy karta tuzilishini takrorlaydi */
function CardSkeleton() {
  return (
    <li
      aria-hidden
      className="flex flex-col gap-3 rounded-[var(--radius-xl)] border border-border bg-surface p-4 md:p-5"
    >
      <div className="flex items-center gap-2">
        <span className="h-4 w-28 animate-pulse rounded-[var(--radius-xs)] bg-surface-2" />
        <span className="h-7 w-16 animate-pulse rounded-full bg-surface-2" />
        <span className="h-7 w-24 animate-pulse rounded-full bg-surface-2" />
        <span className="ml-auto h-9 w-9 animate-pulse rounded-full bg-surface-2" />
      </div>
      <span className="h-5 w-3/4 animate-pulse rounded-[var(--radius-xs)] bg-surface-2" />
      <div className="flex flex-col gap-2 rounded-[var(--radius-md)] border border-border bg-sunk p-3">
        <span className="h-3.5 w-[92%] animate-pulse rounded-[var(--radius-xs)] bg-surface-2" />
        <span className="h-3.5 w-[64%] animate-pulse rounded-[var(--radius-xs)] bg-surface-2" />
      </div>
      <div className="flex gap-2">
        <span className="h-11 w-32 animate-pulse rounded-[var(--radius)] bg-surface-2" />
        <span className="h-11 w-28 animate-pulse rounded-[var(--radius)] bg-surface-2" />
      </div>
    </li>
  );
}

export function ListSkeleton({ rows = 4 }: { rows?: number }) {
  const t = useTranslations("pages.common");
  return (
    <ul
      aria-busy="true"
      aria-label={t("loading")}
      className="flex list-none flex-col gap-3 p-0"
    >
      {Array.from({ length: rows }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </ul>
  );
}

/** Umumiy markazlashgan holat qutisi: ikonka + sarlavha + izoh + amal */
function Panel({
  icon,
  title,
  body,
  action,
  tone = "neutral",
  role,
}: {
  icon: ReactNode;
  title: string;
  body: string;
  action?: ReactNode;
  tone?: "neutral" | "error";
  role?: "alert";
}) {
  return (
    <section
      role={role}
      className="flex flex-col items-center gap-4 rounded-[var(--radius-xl)] border border-border bg-surface px-6 py-12 text-center"
    >
      <span
        className={cn(
          "flex h-16 w-16 items-center justify-center rounded-[18px] border",
          tone === "error"
            ? "border-error bg-error-soft text-error"
            : "border-border-strong bg-surface-2 text-muted",
        )}
      >
        {icon}
      </span>
      <div className="flex max-w-[440px] flex-col gap-2">
        <h2 className="text-headline-sm font-extrabold tracking-tight text-text">
          {title}
        </h2>
        <p className="text-body-md text-muted">{body}</p>
      </div>
      {action}
    </section>
  );
}

export function EmptyState({
  icon,
  title,
  body,
}: {
  icon: ReactNode;
  title: string;
  body: string;
}) {
  const t = useTranslations("pages.common");
  return (
    <Panel
      icon={icon}
      title={title}
      body={body}
      action={
        <Link
          href="/app"
          className={cn(
            buttonVariants({ variant: "primary" }),
            "min-h-11 px-5",
          )}
        >
          {t("goGenerator")}
        </Link>
      }
    />
  );
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  const t = useTranslations("pages.common");
  return (
    <Panel
      role="alert"
      tone="error"
      icon={<AlertTriangle size={26} aria-hidden />}
      title={t("errorTitle")}
      body={message}
      action={
        <Button variant="secondary" className="min-h-11" onClick={onRetry}>
          <RotateCcw size={16} aria-hidden />
          {t("retry")}
        </Button>
      }
    />
  );
}

/** Kirmagan foydalanuvchi: tarix/kutubxona faqat hisobda saqlanadi */
export function SignInState({ next }: { next: string }) {
  const t = useTranslations("pages.common");
  const locale = useLocale();
  return (
    <Panel
      icon={<LogIn size={26} aria-hidden />}
      title={t("signInTitle")}
      body={t("signInBody")}
      action={
        <a
          href={googleLoginUrl(`/${locale}${next}`)}
          className={cn(
            buttonVariants({ variant: "primary" }),
            "min-h-11 px-5",
          )}
        >
          {t("signInAction")}
        </a>
      }
    />
  );
}

export function Pagination({
  page,
  limit,
  total,
  onPage,
}: {
  page: number;
  limit: number;
  total: number;
  onPage: (p: number) => void;
}) {
  const t = useTranslations("pages.common");
  if (!total) return null;
  const from = (page - 1) * limit + 1;
  const to = Math.min(page * limit, total);
  return (
    <nav
      aria-label={t("pagination")}
      className="flex flex-wrap items-center justify-between gap-3"
    >
      <span className="font-mono text-code-sm text-subtle">
        {t("range", { from, to, total })}
      </span>
      <div className="flex gap-2">
        <Button
          variant="secondary"
          className="min-h-11"
          disabled={page <= 1}
          onClick={() => onPage(page - 1)}
        >
          {t("prev")}
        </Button>
        <Button
          variant="secondary"
          className="min-h-11"
          disabled={to >= total}
          onClick={() => onPage(page + 1)}
        >
          {t("next")}
        </Button>
      </div>
    </nav>
  );
}
