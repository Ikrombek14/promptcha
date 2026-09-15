"use client";

// Admin panel uchun umumiy qismlar: karta, boʻlim sarlavhasi, jadval, KPI karta, holatlar, sahifalash.
// Uslub: design/tokens.md — 1px chegara, soya yoʻq, serif sarlavha, mono raqamlar.

import * as React from "react";
import { useTranslations } from "next-intl";
import { motion } from "motion/react";
import { Button } from "@/components/ui/button";
import { Callout, Skeleton } from "@/components/ui/callout";
import { fadeUp } from "@/lib/motion";
import { cn } from "@/lib/utils";

export function Card({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-[var(--radius)] border border-border bg-surface p-4 md:p-6",
        className,
      )}
      {...props}
    />
  );
}

export function SectionTitle({
  children,
  aside,
  className,
}: {
  children: React.ReactNode;
  aside?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "mb-3 flex items-baseline justify-between gap-3",
        className,
      )}
    >
      <h2 className="font-serif text-headline-sm text-text">{children}</h2>
      {aside && (
        <span className="font-mono text-code-sm text-muted">{aside}</span>
      )}
    </div>
  );
}

/** Sahifa kontenti — bir marta fadeUp bilan chiqadi */
export function PageBody({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <motion.div
      variants={fadeUp}
      initial="hidden"
      animate="show"
      className={cn("flex flex-col gap-6", className)}
    >
      {children}
    </motion.div>
  );
}

export function PageTitle({
  children,
  aside,
}: {
  children: React.ReactNode;
  aside?: React.ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <h1 className="font-serif text-headline-md text-text">{children}</h1>
      {aside}
    </div>
  );
}

// --- Holatlar -------------------------------------------------------------

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  const t = useTranslations("admin.common");
  return (
    <Callout
      tone="error"
      role="alert"
      className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"
    >
      <span>
        <span className="font-medium">{t("errorTitle")}: </span>
        {message}
      </span>
      {onRetry && (
        <Button
          variant="secondary"
          size="sm"
          onClick={onRetry}
          className="shrink-0"
        >
          {t("retry")}
        </Button>
      )}
    </Callout>
  );
}

export function EmptyState({ children }: { children?: React.ReactNode }) {
  const t = useTranslations("admin.common");
  return (
    <p className="py-10 text-center text-body-md text-muted">
      {children ?? t("empty")}
    </p>
  );
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="flex flex-col gap-2" aria-busy>
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-10" />
      ))}
    </div>
  );
}

// --- Jadval ----------------------------------------------------------------

export type Column<T> = {
  key: string;
  header: React.ReactNode;
  /** Raqam ustunlari oʻngga, mono */
  numeric?: boolean;
  className?: string;
  render: (row: T) => React.ReactNode;
};

export function Table<T>({
  columns,
  rows,
  rowKey,
  renderAfterRow,
  caption,
}: {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  /** Qator ostida qoʻshimcha qator (inline forma) */
  renderAfterRow?: (row: T) => React.ReactNode;
  caption?: string;
}) {
  return (
    <div className="-mx-4 overflow-x-auto md:-mx-6">
      <table className="w-full min-w-[640px] border-collapse text-body-md text-text">
        {caption && <caption className="sr-only">{caption}</caption>}
        <thead>
          <tr className="border-b border-border">
            {columns.map((c) => (
              <th
                key={c.key}
                scope="col"
                className={cn(
                  "px-4 pb-2 text-label-sm font-medium uppercase tracking-wider text-muted md:px-6",
                  c.numeric ? "text-right" : "text-left",
                  c.className,
                )}
              >
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const k = rowKey(row);
            const after = renderAfterRow?.(row);
            return (
              <React.Fragment key={k}>
                <tr className="border-b border-border last:border-b-0">
                  {columns.map((c) => (
                    <td
                      key={c.key}
                      className={cn(
                        "px-4 py-3 align-top md:px-6",
                        c.numeric && "text-right font-mono tabular-nums",
                        c.className,
                      )}
                    >
                      {c.render(row)}
                    </td>
                  ))}
                </tr>
                {after && (
                  <tr className="border-b border-border bg-surface-2 last:border-b-0">
                    <td colSpan={columns.length} className="px-4 py-3 md:px-6">
                      {after}
                    </td>
                  </tr>
                )}
              </React.Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
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
  const t = useTranslations("admin.common");
  if (total <= limit) return null;
  const from = (page - 1) * limit + 1;
  const to = Math.min(page * limit, total);
  return (
    <nav
      className="mt-4 flex items-center justify-between gap-3"
      aria-label="pagination"
    >
      <span className="font-mono text-code-sm text-muted">
        {t("range", { from, to, total })}
      </span>
      <div className="flex gap-2">
        <Button
          variant="secondary"
          size="sm"
          disabled={page <= 1}
          onClick={() => onPage(page - 1)}
        >
          {t("prev")}
        </Button>
        <Button
          variant="secondary"
          size="sm"
          disabled={to >= total}
          onClick={() => onPage(page + 1)}
        >
          {t("next")}
        </Button>
      </div>
    </nav>
  );
}

// --- KPI -------------------------------------------------------------------

export function Kpi({
  label,
  value,
  parts,
  hint,
}: {
  label: string;
  /** Asosiy raqam (mono, katta) */
  value: string;
  /** Kichik boʻlaklar: [yorliq, qiymat] */
  parts?: [string, string][];
  hint?: string;
}) {
  return (
    <Card className="flex flex-col gap-2">
      <span className="text-label-sm font-medium uppercase tracking-wider text-muted">
        {label}
      </span>
      <span className="font-mono text-headline-md tabular-nums text-text">
        {value}
      </span>
      {parts && (
        <dl className="flex flex-wrap gap-x-4 gap-y-1 font-mono text-code-sm text-muted">
          {parts.map(([k, v]) => (
            <div key={k} className="flex gap-1.5">
              <dt>{k}</dt>
              <dd className="text-text">{v}</dd>
            </div>
          ))}
        </dl>
      )}
      {hint && <span className="text-body-sm text-muted">{hint}</span>}
    </Card>
  );
}

export function KpiSkeleton() {
  return (
    <Card className="flex flex-col gap-2" aria-busy>
      <Skeleton className="h-4 w-1/2" />
      <Skeleton className="h-8 w-2/3" />
      <Skeleton className="h-4 w-full" />
    </Card>
  );
}

/** Maydon yorligʻi + kontent (formalar uchun) */
export function Field({
  label,
  htmlFor,
  help,
  children,
  className,
}: {
  label: React.ReactNode;
  htmlFor?: string;
  help?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col gap-2", className)}>
      <label htmlFor={htmlFor} className="text-body-md font-medium text-text">
        {label}
      </label>
      {children}
      {help && <span className="text-body-sm text-muted">{help}</span>}
    </div>
  );
}

export function Badge({
  tone = "neutral",
  children,
}: {
  tone?: "neutral" | "accent";
  children: React.ReactNode;
}) {
  return (
    <span
      className={cn(
        "inline-flex h-6 items-center rounded-[var(--radius-sm)] border px-2 font-mono text-code-sm",
        tone === "neutral" && "border-border bg-surface-2 text-muted",
        tone === "accent" && "border-accent bg-surface text-text",
      )}
    >
      {children}
    </span>
  );
}
