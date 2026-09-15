"use client";

import { useCallback, useId, useState } from "react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Callout } from "@/components/ui/callout";
import { Input } from "@/components/ui/textarea";
import {
  type AdminUser,
  type GrantBody,
  grantUser,
  listUsers,
} from "@/lib/admin-api";
import {
  errorMessage,
  useDebounced,
  useLoad,
} from "@/components/admin/use-load";
import { parseInt0, parseIntAny, useFmt } from "@/components/admin/format";
import {
  Badge,
  Card,
  EmptyState,
  ErrorState,
  PageBody,
  PageTitle,
  Pagination,
  Table,
  TableSkeleton,
  type Column,
} from "@/components/admin/primitives";

const LIMIT = 50;

type Action = "pro" | "free" | "bonus";
type Open = { id: string; action: Action } | null;

function isProActive(u: AdminUser): boolean {
  if (u.plan !== "pro") return false;
  if (!u.pro_until) return true;
  return new Date(u.pro_until).getTime() > Date.now();
}

/** Qator ostidagi inline forma: Pro (kun), bepulga qaytarish (tasdiq), bonus (son) */
function RowAction({
  user,
  action,
  onDone,
  onClose,
}: {
  user: AdminUser;
  action: Action;
  onDone: (u: AdminUser) => void;
  onClose: () => void;
}) {
  const t = useTranslations("admin.users");
  const tc = useTranslations("admin.common");
  const id = useId();
  const [value, setValue] = useState(action === "pro" ? "30" : "5");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const parsed = action === "bonus" ? parseIntAny(value) : parseInt0(value);
  const valid =
    action === "free" || (parsed !== null && (action !== "pro" || parsed > 0));

  const submit = async () => {
    if (!valid || busy) return;
    const body: GrantBody =
      action === "pro"
        ? { plan: "pro", pro_days: parsed ?? 30 }
        : action === "free"
          ? { plan: "free" }
          : { bonus_generations: parsed ?? 0 };
    setBusy(true);
    setError(null);
    try {
      const updated = await grantUser(user.id, body);
      onDone(updated);
    } catch (e) {
      setError(errorMessage(e));
      setBusy(false);
    }
  };

  return (
    <form
      className="flex flex-col gap-3"
      onSubmit={(e) => {
        e.preventDefault();
        void submit();
      }}
    >
      <div className="flex flex-wrap items-end gap-3">
        {action === "free" ? (
          <p className="text-body-md text-text">
            {t("confirmFree", { email: user.email })}
          </p>
        ) : (
          <div className="flex flex-col gap-1">
            <label htmlFor={id} className="text-body-sm text-muted">
              {action === "pro" ? t("proDays") : t("bonusCount")}
            </label>
            <Input
              id={id}
              type="number"
              inputMode="numeric"
              min={action === "pro" ? 1 : undefined}
              step={1}
              value={value}
              onChange={(e) => setValue(e.target.value)}
              className="w-32 font-mono"
              autoFocus
              disabled={busy}
            />
          </div>
        )}
        <div className="flex gap-2">
          <Button
            type="submit"
            variant="primary"
            size="md"
            disabled={!valid || busy}
          >
            {action === "pro"
              ? t("give")
              : action === "free"
                ? t("yesFree")
                : t("add")}
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="md"
            onClick={onClose}
            disabled={busy}
          >
            {tc("cancel")}
          </Button>
        </div>
      </div>
      {!valid && (
        <span className="text-body-sm text-error">{tc("invalidNumber")}</span>
      )}
      {error && <ErrorState message={error} />}
    </form>
  );
}

export function Users() {
  const t = useTranslations("admin");
  const tu = useTranslations("admin.users");
  const f = useFmt();
  const [q, setQ] = useState("");
  const dq = useDebounced(q.trim(), 400);
  const [page, setPage] = useState(1);
  const [open, setOpen] = useState<Open>(null);
  const [flash, setFlash] = useState<string | null>(null);
  const searchId = useId();

  const loader = useCallback(
    () => listUsers({ q: dq, page, limit: LIMIT }),
    [dq, page],
  );
  const { data, error, loading, reload, setData } = useLoad(loader);

  const onSearch = (v: string) => {
    setQ(v);
    setPage(1);
    setOpen(null);
  };

  const onDone = (u: AdminUser) => {
    setData((prev) => ({
      ...prev,
      items: prev.items.map((x) => (x.id === u.id ? u : x)),
    }));
    setOpen(null);
    setFlash(u.id);
  };

  const actionButtons = (u: AdminUser) => (
    <div className="flex flex-wrap gap-2">
      {isProActive(u) ? (
        <Button size="sm" onClick={() => setOpen({ id: u.id, action: "free" })}>
          {tu("toFree")}
        </Button>
      ) : (
        <Button size="sm" onClick={() => setOpen({ id: u.id, action: "pro" })}>
          {tu("grantPro")}
        </Button>
      )}
      <Button size="sm" onClick={() => setOpen({ id: u.id, action: "bonus" })}>
        {tu("addBonus")}
      </Button>
    </div>
  );

  const cols: Column<AdminUser>[] = [
    {
      key: "user",
      header: tu("cols.user"),
      render: (u) => (
        <div className="flex flex-col">
          <span className="flex items-center gap-2">
            <span className="text-text">{u.email}</span>
            {u.is_admin && <Badge>{tu("adminBadge")}</Badge>}
            {flash === u.id && (
              <span className="font-mono text-code-sm text-accent">
                {tu("updated")}
              </span>
            )}
          </span>
          {u.name && <span className="text-body-sm text-muted">{u.name}</span>}
        </div>
      ),
    },
    {
      key: "plan",
      header: tu("cols.plan"),
      render: (u) => (
        <div className="flex flex-col gap-1">
          <span>
            <Badge tone={isProActive(u) ? "accent" : "neutral"}>
              {tu(`plan.${u.plan}`)}
            </Badge>
          </span>
          {u.plan === "pro" && u.pro_until && (
            <span className="font-mono text-code-sm text-muted">
              {tu("proUntil", { date: f.date(u.pro_until) })}
            </span>
          )}
        </div>
      ),
    },
    {
      key: "bonus",
      header: tu("cols.bonus"),
      numeric: true,
      render: (u) => f.n(u.bonus_generations),
    },
    {
      key: "gen",
      header: tu("cols.generations"),
      numeric: true,
      render: (u) => f.n(u.generations_total),
    },
    {
      key: "tokens",
      header: tu("cols.tokens"),
      numeric: true,
      render: (u) => (
        <span>
          {f.n(u.input_tokens)} <span className="text-muted">/</span>{" "}
          {f.n(u.output_tokens)}
        </span>
      ),
    },
    {
      key: "login",
      header: tu("cols.lastLogin"),
      render: (u) => (
        <span className="font-mono text-code-md text-muted">
          {f.dateTime(u.last_login_at)}
        </span>
      ),
    },
    { key: "actions", header: tu("cols.actions"), render: actionButtons },
  ];

  return (
    <PageBody>
      <PageTitle
        aside={
          <div className="w-full sm:w-80">
            <label htmlFor={searchId} className="sr-only">
              {tu("searchLabel")}
            </label>
            <Input
              id={searchId}
              type="search"
              value={q}
              onChange={(e) => onSearch(e.target.value)}
              placeholder={tu("searchPlaceholder")}
              autoComplete="off"
            />
          </div>
        }
      >
        {t("nav.users")}
      </PageTitle>

      <Card>
        {error ? (
          <ErrorState message={error} onRetry={reload} />
        ) : loading || !data ? (
          <TableSkeleton rows={8} />
        ) : data.items.length === 0 ? (
          <EmptyState>{dq ? t("common.notFound") : undefined}</EmptyState>
        ) : (
          <>
            <Table
              columns={cols}
              rows={data.items}
              rowKey={(u) => u.id}
              caption={t("nav.users")}
              renderAfterRow={(u) =>
                open && open.id === u.id ? (
                  <RowAction
                    key={`${u.id}-${open.action}`}
                    user={u}
                    action={open.action}
                    onDone={onDone}
                    onClose={() => setOpen(null)}
                  />
                ) : null
              }
            />
            <Pagination
              page={data.page}
              limit={data.limit}
              total={data.total}
              onPage={(p) => {
                setPage(p);
                setOpen(null);
              }}
            />
          </>
        )}
      </Card>
      {flash && data && !data.items.some((u) => u.id === flash) && (
        <Callout tone="accent">{tu("updated")}</Callout>
      )}
    </PageBody>
  );
}
