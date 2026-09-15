"use client";

import { useCallback, useState } from "react";
import { useTranslations } from "next-intl";
import { LayoutGroup } from "motion/react";
import { Chip } from "@/components/ui/chip";
import { Skeleton } from "@/components/ui/callout";
import { type AdminStats, getStats } from "@/lib/admin-api";
import { useLoad } from "@/components/admin/use-load";
import { useFmt } from "@/components/admin/format";
import {
  Card,
  EmptyState,
  ErrorState,
  Kpi,
  KpiSkeleton,
  PageBody,
  PageTitle,
  SectionTitle,
  Table,
  TableSkeleton,
  type Column,
} from "@/components/admin/primitives";
import { cn } from "@/lib/utils";

const PERIODS = [7, 30, 90] as const;

function DailyBars({ daily }: { daily: AdminStats["daily"] }) {
  const t = useTranslations("admin.overview");
  const f = useFmt();
  if (!daily.length) return <EmptyState />;
  const max = Math.max(1, ...daily.map((d) => d.generations));
  const last = daily.length - 1;
  return (
    <div>
      <div
        className="flex h-40 items-end gap-px"
        role="img"
        aria-label={t("daily")}
      >
        {daily.map((d, i) => {
          const h = Math.max(2, Math.round((d.generations / max) * 100));
          const tokens = d.input_tokens + d.output_tokens;
          return (
            <div
              key={d.date}
              className="group flex h-full flex-1 items-end"
              title={t("dailyTip", {
                date: d.date,
                n: f.n(d.generations),
                tokens: f.n(tokens),
              })}
            >
              <div
                className={cn(
                  "w-full rounded-t-[var(--radius-xs)] transition-colors duration-200",
                  i === last ? "bg-accent" : "bg-border group-hover:bg-muted",
                )}
                style={{ height: `${h}%` }}
              />
            </div>
          );
        })}
      </div>
      <div className="mt-2 flex justify-between font-mono text-code-sm text-muted">
        <span>{f.shortDay(daily[0].date)}</span>
        <span>{f.shortDay(daily[last].date)}</span>
      </div>
    </div>
  );
}

export function Overview() {
  const t = useTranslations("admin");
  const to = useTranslations("admin.overview");
  const tc = useTranslations("admin.overview.cols");
  const f = useFmt();
  const [days, setDays] = useState<number>(30);
  const loader = useCallback(() => getStats(days), [days]);
  const { data, error, loading, reload } = useLoad(loader);

  const periodChips = (
    <LayoutGroup id="admin-period">
      <div
        className="flex items-center gap-2"
        role="group"
        aria-label={to("period")}
      >
        <span className="mr-1 text-label-sm font-medium uppercase tracking-wider text-muted">
          {to("period")}
        </span>
        {PERIODS.map((p) => (
          <Chip
            key={p}
            selected={days === p}
            indicatorId="admin-period"
            onClick={() => setDays(p)}
          >
            {to("days", { n: p })}
          </Chip>
        ))}
      </div>
    </LayoutGroup>
  );

  const periodGenerations = data
    ? data.daily.reduce((s, d) => s + d.generations, 0)
    : 0;
  const periodTokens = data ? data.tokens.input + data.tokens.output : 0;
  const avg =
    periodGenerations > 0 ? Math.round(periodTokens / periodGenerations) : null;

  const toolCols: Column<AdminStats["by_tool"][number]>[] = [
    { key: "ai", header: tc("tool"), render: (r) => r.ai },
    {
      key: "g",
      header: tc("generations"),
      numeric: true,
      render: (r) => f.n(r.generations),
    },
    {
      key: "i",
      header: tc("input"),
      numeric: true,
      render: (r) => f.n(r.input_tokens),
    },
    {
      key: "o",
      header: tc("output"),
      numeric: true,
      render: (r) => f.n(r.output_tokens),
    },
  ];
  const providerCols: Column<AdminStats["by_provider"][number]>[] = [
    { key: "p", header: tc("provider"), render: (r) => r.provider },
    {
      key: "m",
      header: tc("model"),
      render: (r) => <span className="font-mono text-code-md">{r.model}</span>,
    },
    {
      key: "c",
      header: tc("calls"),
      numeric: true,
      render: (r) => f.n(r.calls),
    },
    {
      key: "i",
      header: tc("input"),
      numeric: true,
      render: (r) =>
        r.estimated_calls > 0 ? `~${f.n(r.input_tokens)}` : f.n(r.input_tokens),
    },
    {
      key: "o",
      header: tc("output"),
      numeric: true,
      render: (r) =>
        r.estimated_calls > 0
          ? `~${f.n(r.output_tokens)}`
          : f.n(r.output_tokens),
    },
  ];
  const stageCols: Column<AdminStats["by_stage"][number]>[] = [
    {
      key: "s",
      header: tc("stage"),
      render: (r) => <span className="font-mono text-code-md">{r.stage}</span>,
    },
    {
      key: "c",
      header: tc("calls"),
      numeric: true,
      render: (r) => f.n(r.calls),
    },
    {
      key: "i",
      header: tc("input"),
      numeric: true,
      render: (r) => f.n(r.input_tokens),
    },
    {
      key: "o",
      header: tc("output"),
      numeric: true,
      render: (r) => f.n(r.output_tokens),
    },
  ];
  const userCols: Column<AdminStats["top_users"][number]>[] = [
    { key: "u", header: tc("user"), render: (r) => r.email },
    {
      key: "g",
      header: tc("generations"),
      numeric: true,
      render: (r) => f.n(r.generations),
    },
    {
      key: "i",
      header: tc("input"),
      numeric: true,
      render: (r) => f.n(r.input_tokens),
    },
    {
      key: "o",
      header: tc("output"),
      numeric: true,
      render: (r) => f.n(r.output_tokens),
    },
  ];

  const hasEstimated = !!data?.by_provider.some((p) => p.estimated_calls > 0);

  return (
    <PageBody>
      <PageTitle aside={periodChips}>{t("nav.overview")}</PageTitle>

      {error && <ErrorState message={error} onRetry={reload} />}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {loading || !data ? (
          <>
            <KpiSkeleton />
            <KpiSkeleton />
            <KpiSkeleton />
            <KpiSkeleton />
          </>
        ) : (
          <>
            <Kpi
              label={to("activeUsers")}
              value={f.n(data.active_users.today)}
              parts={[
                [to("today"), f.n(data.active_users.today)],
                [to("d7"), f.n(data.active_users.d7)],
                [to("d30"), f.n(data.active_users.d30)],
              ]}
            />
            <Kpi
              label={to("generations")}
              value={f.n(data.generations.today)}
              parts={[
                [to("today"), f.n(data.generations.today)],
                [to("d7"), f.n(data.generations.d7)],
                [to("d30"), f.n(data.generations.d30)],
              ]}
            />
            <Kpi
              label={to("tokens")}
              value={f.n(periodTokens)}
              parts={[
                [to("input"), f.n(data.tokens.input)],
                [to("output"), f.n(data.tokens.output)],
              ]}
              hint={to("days", { n: data.days })}
            />
            <Kpi
              label={to("avgTokens")}
              value={f.n(avg)}
              hint={to("avgHint")}
            />
          </>
        )}
      </div>

      <Card>
        <SectionTitle aside={data ? to("days", { n: data.days }) : undefined}>
          {to("daily")}
        </SectionTitle>
        {loading || !data ? (
          <Skeleton className="h-40" aria-busy />
        ) : (
          <DailyBars daily={data.daily} />
        )}
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <SectionTitle>{to("byTool")}</SectionTitle>
          {loading || !data ? (
            <TableSkeleton rows={4} />
          ) : data.by_tool.length ? (
            <Table
              columns={toolCols}
              rows={data.by_tool}
              rowKey={(r) => r.ai}
              caption={to("byTool")}
            />
          ) : (
            <EmptyState />
          )}
        </Card>
        <Card>
          <SectionTitle>{to("byStage")}</SectionTitle>
          {loading || !data ? (
            <TableSkeleton rows={4} />
          ) : data.by_stage.length ? (
            <Table
              columns={stageCols}
              rows={data.by_stage}
              rowKey={(r) => r.stage}
              caption={to("byStage")}
            />
          ) : (
            <EmptyState />
          )}
        </Card>
      </div>

      <Card>
        <SectionTitle
          aside={hasEstimated ? t("common.estimatedHint") : undefined}
        >
          {to("byProvider")}
        </SectionTitle>
        {loading || !data ? (
          <TableSkeleton rows={4} />
        ) : data.by_provider.length ? (
          <Table
            columns={providerCols}
            rows={data.by_provider}
            rowKey={(r) => `${r.provider}/${r.model}`}
            caption={to("byProvider")}
          />
        ) : (
          <EmptyState />
        )}
      </Card>

      <Card>
        <SectionTitle>{to("topUsers")}</SectionTitle>
        {loading || !data ? (
          <TableSkeleton rows={5} />
        ) : data.top_users.length ? (
          <Table
            columns={userCols}
            rows={data.top_users}
            rowKey={(r) => r.user_id}
            caption={to("topUsers")}
          />
        ) : (
          <EmptyState />
        )}
      </Card>
    </PageBody>
  );
}
