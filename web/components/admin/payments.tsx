"use client";

import { useCallback, useId, useState } from "react";
import { useTranslations } from "next-intl";
import { LayoutGroup } from "motion/react";
import { Button } from "@/components/ui/button";
import { Callout } from "@/components/ui/callout";
import { Chip } from "@/components/ui/chip";
import { Input } from "@/components/ui/textarea";
import {
  type AdminUser,
  type Payment,
  type PaymentMethod,
  createPayment,
  listPayments,
  listUsers,
} from "@/lib/admin-api";
import {
  errorMessage,
  useDebounced,
  useLoad,
} from "@/components/admin/use-load";
import { parseInt0, useFmt } from "@/components/admin/format";
import {
  Card,
  EmptyState,
  ErrorState,
  Field,
  PageBody,
  PageTitle,
  Pagination,
  SectionTitle,
  Table,
  TableSkeleton,
  type Column,
} from "@/components/admin/primitives";

const LIMIT = 50;
const METHODS: PaymentMethod[] = ["manual", "payme", "click"];

/** Email boʻyicha foydalanuvchi tanlash: input → roʻyxat → tanlangan */
function UserPicker({
  value,
  onChange,
  disabled,
}: {
  value: AdminUser | null;
  onChange: (u: AdminUser | null) => void;
  disabled?: boolean;
}) {
  const tp = useTranslations("admin.payments");
  const tc = useTranslations("admin.common");
  const id = useId();
  const [q, setQ] = useState("");
  const dq = useDebounced(q.trim(), 400);
  const loader = useCallback(
    () => (dq ? listUsers({ q: dq, limit: 8 }) : Promise.resolve(null)),
    [dq],
  );
  const { data, error, loading } = useLoad(loader);

  if (value) {
    return (
      <Field label={tp("user")}>
        <div className="flex h-10 items-center justify-between gap-3 rounded-[var(--radius)] border border-accent bg-surface px-3">
          <span className="truncate text-body-md text-text">{value.email}</span>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onChange(null)}
            disabled={disabled}
          >
            {tp("change")}
          </Button>
        </div>
      </Field>
    );
  }

  return (
    <Field label={tp("user")} htmlFor={id} help={tp("selectUser")}>
      <Input
        id={id}
        type="search"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder={tp("userSearch")}
        autoComplete="off"
        disabled={disabled}
      />
      {dq && (
        <div
          className="rounded-[var(--radius)] border border-border bg-surface"
          role="listbox"
          aria-label={tp("user")}
        >
          {error ? (
            <p className="px-3 py-2 text-body-sm text-error">{error}</p>
          ) : loading ? (
            <p className="px-3 py-2 text-body-sm text-muted">{tc("loading")}</p>
          ) : !data || data.items.length === 0 ? (
            <p className="px-3 py-2 text-body-sm text-muted">
              {tc("notFound")}
            </p>
          ) : (
            data.items.map((u) => (
              <button
                key={u.id}
                type="button"
                role="option"
                aria-selected={false}
                onClick={() => {
                  onChange(u);
                  setQ("");
                }}
                className="flex w-full flex-col items-start border-b border-border px-3 py-2 text-left last:border-b-0 hover:bg-surface-2"
              >
                <span className="text-body-md text-text">{u.email}</span>
                {u.name && (
                  <span className="text-body-sm text-muted">{u.name}</span>
                )}
              </button>
            ))
          )}
        </div>
      )}
    </Field>
  );
}

function PaymentForm({ onCreated }: { onCreated: (p: Payment) => void }) {
  const tp = useTranslations("admin.payments");
  const tc = useTranslations("admin.common");
  const ids = { amount: useId(), days: useId(), note: useId() };
  const [user, setUser] = useState<AdminUser | null>(null);
  const [amount, setAmount] = useState("");
  const [days, setDays] = useState("30");
  const [method, setMethod] = useState<PaymentMethod>("manual");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState<Payment | null>(null);

  const amountN = parseInt0(amount);
  const daysN = parseInt0(days);
  const valid = !!user && amountN !== null && daysN !== null && daysN > 0;

  const submit = async () => {
    if (!valid || !user || busy) return;
    setBusy(true);
    setError(null);
    setCreated(null);
    try {
      const p = await createPayment({
        user_id: user.id,
        amount: amountN ?? 0,
        method,
        days: daysN ?? 30,
        note: note.trim() || undefined,
      });
      setCreated(p);
      setUser(null);
      setAmount("");
      setDays("30");
      setMethod("manual");
      setNote("");
      onCreated(p);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card>
      <SectionTitle>{tp("addTitle")}</SectionTitle>
      <form
        className="flex flex-col gap-4"
        onSubmit={(e) => {
          e.preventDefault();
          void submit();
        }}
      >
        <div className="grid gap-4 md:grid-cols-2">
          <UserPicker value={user} onChange={setUser} disabled={busy} />
          <div className="grid grid-cols-2 gap-4">
            <Field label={tp("amount")} htmlFor={ids.amount}>
              <Input
                id={ids.amount}
                type="number"
                inputMode="numeric"
                min={0}
                step={1}
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="font-mono"
                disabled={busy}
                required
              />
            </Field>
            <Field label={tp("days")} htmlFor={ids.days}>
              <Input
                id={ids.days}
                type="number"
                inputMode="numeric"
                min={1}
                step={1}
                value={days}
                onChange={(e) => setDays(e.target.value)}
                className="font-mono"
                disabled={busy}
                required
              />
            </Field>
          </div>
          <Field label={tp("method")}>
            <LayoutGroup id="admin-method">
              <div
                className="flex flex-wrap gap-2"
                role="group"
                aria-label={tp("method")}
              >
                {METHODS.map((m) => (
                  <Chip
                    key={m}
                    tone="outline"
                    selected={method === m}
                    indicatorId="admin-method"
                    onClick={() => setMethod(m)}
                    disabled={busy}
                  >
                    {tp(`methods.${m}`)}
                  </Chip>
                ))}
              </div>
            </LayoutGroup>
          </Field>
          <Field label={tp("note")} htmlFor={ids.note}>
            <Input
              id={ids.note}
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder={tp("notePlaceholder")}
              maxLength={200}
              disabled={busy}
            />
          </Field>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <Button
            type="submit"
            variant="primary"
            size="lg"
            disabled={!valid || busy}
          >
            {busy ? tp("submitting") : tp("submit")}
          </Button>
          {!valid && amount && amountN === null && (
            <span className="text-body-sm text-error">
              {tc("invalidNumber")}
            </span>
          )}
        </div>
        {error && <ErrorState message={error} />}
        {created && (
          <Callout tone="accent" role="status">
            {tp("created", { email: created.email, days: created.days })}
          </Callout>
        )}
      </form>
    </Card>
  );
}

export function Payments() {
  const t = useTranslations("admin");
  const tp = useTranslations("admin.payments");
  const f = useFmt();
  const [page, setPage] = useState(1);
  const loader = useCallback(
    () => listPayments({ page, limit: LIMIT }),
    [page],
  );
  const { data, error, loading, reload } = useLoad(loader);

  const cols: Column<Payment>[] = [
    {
      key: "date",
      header: tp("cols.date"),
      render: (p) => (
        <span className="font-mono text-code-md text-muted">
          {f.dateTime(p.paid_at)}
        </span>
      ),
    },
    { key: "user", header: tp("cols.user"), render: (p) => p.email },
    {
      key: "amount",
      header: tp("cols.amount"),
      numeric: true,
      render: (p) => (
        <span>
          {f.n(p.amount)} <span className="text-muted">{p.currency}</span>
        </span>
      ),
    },
    {
      key: "method",
      header: tp("cols.method"),
      render: (p) => tp(`methods.${p.method}`),
    },
    {
      key: "days",
      header: tp("cols.days"),
      numeric: true,
      render: (p) => f.n(p.days),
    },
    {
      key: "note",
      header: tp("cols.note"),
      render: (p) => <span className="text-muted">{p.note ?? "—"}</span>,
    },
    {
      key: "by",
      header: tp("cols.by"),
      render: (p) => <span className="text-muted">{p.created_by}</span>,
    },
  ];

  return (
    <PageBody>
      <PageTitle>{t("nav.payments")}</PageTitle>

      <PaymentForm
        onCreated={() => {
          setPage(1);
          reload();
        }}
      />

      <Card>
        <SectionTitle aside={data ? f.n(data.total) : undefined}>
          {tp("listTitle")}
        </SectionTitle>
        {error ? (
          <ErrorState message={error} onRetry={reload} />
        ) : loading || !data ? (
          <TableSkeleton rows={6} />
        ) : data.items.length === 0 ? (
          <EmptyState />
        ) : (
          <>
            <Table
              columns={cols}
              rows={data.items}
              rowKey={(p) => p.id}
              caption={tp("listTitle")}
            />
            <Pagination
              page={data.page}
              limit={data.limit}
              total={data.total}
              onPage={setPage}
            />
          </>
        )}
      </Card>
    </PageBody>
  );
}
