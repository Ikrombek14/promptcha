"use client";

import { useCallback, useId, useState } from "react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/callout";
import {
  type AdminSettings,
  LIMIT_KEYS,
  type LimitKey,
  getSettings,
  updateSettings,
} from "@/lib/admin-api";
import { errorMessage, useLoad } from "@/components/admin/use-load";
import { parseInt0, useFmt } from "@/components/admin/format";
import {
  Card,
  ErrorState,
  Field,
  PageBody,
  PageTitle,
} from "@/components/admin/primitives";

type Form = Record<LimitKey, string>;

function toForm(s: AdminSettings): Form {
  return {
    guest_total_generations: String(s.guest_total_generations),
    guest_daily_ip_generations: String(s.guest_daily_ip_generations),
    free_daily_generations: String(s.free_daily_generations),
  };
}

function SettingsForm({
  initial,
  onSaved,
}: {
  initial: AdminSettings;
  onSaved: (s: AdminSettings) => void;
}) {
  const ts = useTranslations("admin.settings");
  const tc = useTranslations("admin.common");
  const f = useFmt();
  const prefix = useId();
  const [form, setForm] = useState<Form>(() => toForm(initial));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const parsed = Object.fromEntries(
    LIMIT_KEYS.map((k) => [k, parseInt0(form[k])]),
  ) as Record<LimitKey, number | null>;
  const invalid = LIMIT_KEYS.filter((k) => parsed[k] === null);
  const changed = LIMIT_KEYS.filter(
    (k) => parsed[k] !== null && parsed[k] !== initial[k],
  );
  const canSave = invalid.length === 0 && changed.length > 0 && !busy;

  const submit = async () => {
    if (!canSave) return;
    setBusy(true);
    setError(null);
    setSaved(false);
    try {
      const body = Object.fromEntries(
        changed.map((k) => [k, parsed[k] as number]),
      );
      const next = await updateSettings(body);
      setForm(toForm(next));
      setSaved(true);
      onSaved(next);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <form
      className="flex flex-col gap-6"
      onSubmit={(e) => {
        e.preventDefault();
        void submit();
      }}
    >
      <p className="text-body-md text-muted">{ts("intro")}</p>
      <div className="grid gap-6 md:grid-cols-3">
        {LIMIT_KEYS.map((k) => {
          const id = `${prefix}-${k}`;
          const bad = invalid.includes(k);
          return (
            <Field key={k} label={ts(k)} htmlFor={id} help={ts(`${k}_help`)}>
              <div className="flex items-center gap-3">
                <Input
                  id={id}
                  type="number"
                  inputMode="numeric"
                  min={0}
                  step={1}
                  value={form[k]}
                  onChange={(e) => {
                    const v = e.target.value;
                    setForm((prev) => ({ ...prev, [k]: v }));
                    setSaved(false);
                  }}
                  aria-invalid={bad || undefined}
                  className={
                    bad ? "w-32 border-error font-mono" : "w-32 font-mono"
                  }
                  disabled={busy}
                />
                <span className="whitespace-nowrap font-mono text-code-sm text-muted">
                  {ts("default", { n: f.n(initial.defaults[k]) })}
                </span>
              </div>
              {bad && (
                <span className="text-body-sm text-error">
                  {tc("invalidNumber")}
                </span>
              )}
            </Field>
          );
        })}
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <Button type="submit" variant="primary" size="lg" disabled={!canSave}>
          {busy ? ts("saving") : ts("save")}
        </Button>
        {saved && (
          <span role="status" className="font-mono text-code-sm text-accent">
            {ts("saved")}
          </span>
        )}
      </div>
      {error && <ErrorState message={error} />}
    </form>
  );
}

export function Settings() {
  const t = useTranslations("admin");
  const loader = useCallback(() => getSettings(), []);
  const { data, error, loading, reload, setData } = useLoad(loader);

  return (
    <PageBody>
      <PageTitle>{t("nav.settings")}</PageTitle>
      <Card>
        {error ? (
          <ErrorState message={error} onRetry={reload} />
        ) : loading || !data ? (
          <div className="flex flex-col gap-6" aria-busy>
            <Skeleton className="h-6 w-2/3" />
            <div className="grid gap-6 md:grid-cols-3">
              <Skeleton className="h-24" />
              <Skeleton className="h-24" />
              <Skeleton className="h-24" />
            </div>
            <Skeleton className="h-11 w-40" />
          </div>
        ) : (
          <SettingsForm
            key={JSON.stringify(data)}
            initial={data}
            onSaved={(s) => setData(() => s)}
          />
        )}
      </Card>
    </PageBody>
  );
}
