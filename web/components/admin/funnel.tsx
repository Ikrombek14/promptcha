"use client";

import { useCallback, useState } from "react";
import { useTranslations } from "next-intl";
import { LayoutGroup } from "motion/react";
import { Chip } from "@/components/ui/chip";
import { Skeleton } from "@/components/ui/callout";
import { type AdminFunnel, getFunnel } from "@/lib/admin-api";
import { useLoad } from "@/components/admin/use-load";
import { useFmt } from "@/components/admin/format";
import {
  Card,
  EmptyState,
  ErrorState,
  PageBody,
  PageTitle,
  SectionTitle,
  Table,
  type Column,
} from "@/components/admin/primitives";

const PERIODS = [7, 30, 90] as const;

/** Voronka qadamlari: gʻoya → prompt → nusxa → «ishladi» (A.1 hodisalari). */
export function Funnel() {
  const t = useTranslations("admin.funnel");
  const f = useFmt();
  const [days, setDays] = useState<number>(30);
  const loader = useCallback(() => getFunnel(days), [days]);
  const { loading, data, error, reload } = useLoad(loader);

  const first = data?.steps[0]?.sessions ?? 0;
  const pct = (n: number) => (first > 0 ? Math.round((n / first) * 100) : 0);

  const kindCols: Column<AdminFunnel["by_kind"][number]>[] = [
    { key: "kind", header: t("kind"), render: (r) => r.kind },
    { key: "count", header: t("count"), numeric: true, render: (r) => f.n(r.count) },
    {
      key: "avg",
      header: t("avgScore"),
      numeric: true,
      render: (r) => (r.avg_score === null ? "—" : String(r.avg_score)),
    },
  ];

  return (
    <PageBody>
      <PageTitle
        aside={
          <LayoutGroup id="funnel-period">
            <div className="flex gap-2">
              {PERIODS.map((d) => (
                <Chip
                  key={d}
                  selected={days === d}
                  indicatorId="funnel-period"
                  onClick={() => setDays(d)}
                >
                  {t("days", { n: d })}
                </Chip>
              ))}
            </div>
          </LayoutGroup>
        }
      >
        {t("title")}
      </PageTitle>

      {error && <ErrorState message={error} onRetry={reload} />}

      {loading && !error && (
        <div className="flex flex-col gap-3">
          <Skeleton className="h-40" />
          <Skeleton className="h-56" />
        </div>
      )}

      {data && !error && (
        <div className="flex flex-col gap-6">
          <section>
            <SectionTitle aside={t("bySession")}>{t("steps")}</SectionTitle>
            <Card className="flex flex-col gap-3">
              {data.steps.map((s) => (
                <div key={s.name} className="flex items-center gap-3">
                  <span className="w-40 shrink-0 text-body-sm text-text-2">
                    {t(`step.${s.name}`)}
                  </span>
                  <span
                    aria-hidden
                    className="h-6 min-w-1 rounded-[var(--radius-xs)] bg-accent/70"
                    style={{ width: `${Math.max(pct(s.sessions), 1)}%` }}
                  />
                  <span className="ml-auto shrink-0 font-mono text-code-sm tabular-nums text-text">
                    {f.n(s.sessions)}
                    <span className="ml-2 text-muted">{pct(s.sessions)}%</span>
                  </span>
                </div>
              ))}
              {first === 0 && <EmptyState>{t("empty")}</EmptyState>}
            </Card>
          </section>

          <section>
            <SectionTitle>{t("byKind")}</SectionTitle>
            {data.by_kind.length ? (
              <Table columns={kindCols} rows={data.by_kind} rowKey={(r) => r.kind} />
            ) : (
              <EmptyState>{t("empty")}</EmptyState>
            )}
          </section>

          <section>
            <SectionTitle aside={t("feedbackHint")}>{t("feedback")}</SectionTitle>
            <Card className="flex flex-wrap gap-x-8 gap-y-2 font-mono text-code-sm">
              <span>
                {t("worked")}:{" "}
                <span className="text-quality">{f.n(data.feedback.worked ?? 0)}</span>
              </span>
              <span>
                {t("notWorked")}:{" "}
                <span className="text-error">{f.n(data.feedback.not_worked ?? 0)}</span>
              </span>
            </Card>
          </section>
        </div>
      )}
    </PageBody>
  );
}
