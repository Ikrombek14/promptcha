"use client";

import { useTranslations } from "next-intl";
import { motion, useReducedMotion } from "motion/react";
import {
  AlertTriangle,
  ArrowRight,
  Check,
  Copy,
  HelpCircle,
  LoaderCircle,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { AI_META, type AiTool } from "@/lib/ai-tools";
import type { Stage } from "@/lib/draft";
import { fadeUp, stagger } from "@/lib/motion";
import { cn } from "@/lib/utils";

const panel =
  "flex min-h-80 min-w-0 flex-col gap-6 rounded-[var(--radius-xl)] border border-border bg-surface p-5 md:p-7";

/** Boʻsh holat: nima boʻlishini aytadi va uchta namuna taklif qiladi. */
export function EmptyResult({ onExample }: { onExample: (text: string) => void }) {
  const t = useTranslations("result");
  const examples = useTranslations("examples");
  const reduce = useReducedMotion();
  const items = [0, 1, 2].map((i) => ({
    tag: examples(`${i}.tag`),
    text: examples(`${i}.text`),
  }));

  return (
    <motion.section
      aria-labelledby="e-h"
      className={panel}
      variants={stagger}
      initial={reduce ? false : "hidden"}
      animate="show"
    >
      <div className="flex items-center gap-2.5">
        <h2 className="text-headline-sm font-extrabold tracking-[-0.02em] text-text md:text-headline-md">
          {t("title")}
        </h2>
        <span className="inline-flex h-6.5 items-center gap-1.5 rounded-full border border-border bg-surface-2 px-2.5 text-label-sm font-bold text-muted">
          <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-subtle" />
          {t("noModel")}
        </span>
      </div>

      <div className="flex flex-1 flex-col items-center justify-center gap-4 px-2 py-6 text-center md:px-10">
        <motion.div
          variants={fadeUp}
          className="flex h-16 w-16 items-center justify-center rounded-[18px] border border-[color-mix(in_oklab,var(--accent),var(--border)_55%)] bg-accent-soft text-accent"
        >
          <Sparkles size={28} strokeWidth={1.6} />
        </motion.div>
        <motion.div variants={fadeUp} className="flex max-w-md flex-col gap-2">
          <h3
            id="e-h"
            className="text-headline-sm font-extrabold tracking-[-0.015em] text-text"
          >
            {t("emptyTitle")}
          </h3>
          <p className="text-body-md text-muted">{t("emptyBody")}</p>
        </motion.div>

        <motion.div
          variants={fadeUp}
          className="mt-2 flex w-full max-w-lg flex-col gap-2"
          role="group"
          aria-label={t("examplesLabel")}
        >
          {items.map((e) => (
            <button
              key={e.text}
              type="button"
              onClick={() => onExample(e.text)}
              className="flex min-h-13 items-center gap-3 rounded-[var(--radius-lg)] border border-border-strong bg-surface-2 p-3 px-4 text-left text-body-sm font-semibold text-text-2 transition-colors hover:border-selected-border hover:bg-[var(--selected-bg)] hover:text-text"
            >
              <span className="inline-flex h-6 shrink-0 items-center rounded-[var(--radius-sm)] bg-accent-soft px-2 text-label-sm font-bold text-accent">
                {e.tag}
              </span>
              <span className="flex-1">{e.text}</span>
              <ArrowRight size={16} className="shrink-0 text-subtle" />
            </button>
          ))}
        </motion.div>
      </div>
    </motion.section>
  );
}

/** Savollar bor — javob chapda beriladi. */
export function ClarifyWaiting() {
  const t = useTranslations("result");
  return (
    <section className={cn(panel, "items-center justify-center text-center")}>
      <div className="flex max-w-md flex-col items-center gap-4">
        <span className="flex h-16 w-16 items-center justify-center rounded-[18px] border border-[color-mix(in_oklab,var(--accent),var(--border)_55%)] bg-accent-soft text-accent">
          <HelpCircle size={28} strokeWidth={1.6} />
        </span>
        <h2 className="text-headline-sm font-extrabold tracking-[-0.015em] text-text">
          {t("clarifyTitle")}
        </h2>
        <p className="text-body-md text-muted">{t("clarifyBody")}</p>
      </div>
    </section>
  );
}

const STEPS = [
  { key: "Analyze", stages: ["classify", "clarify"] },
  { key: "Write", stages: ["generate"] },
  { key: "Check", stages: ["explain"] },
] as const;

/** Yuklanish: uch bosqich koʻrsatkichi + skelet. */
export function LoadingResult({ stage, ai }: { stage: Stage | null; ai: AiTool | null }) {
  const t = useTranslations("result");
  const current = STEPS.findIndex((s) =>
    (s.stages as readonly string[]).includes(stage ?? "classify"),
  );
  const active = current === -1 ? 0 : current;
  const meta = ai ? AI_META[ai] : null;

  return (
    <section aria-busy aria-labelledby="l-h" className={panel}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2.5">
          <h2
            id="l-h"
            className="text-headline-sm font-extrabold tracking-[-0.02em] text-text md:text-headline-md"
          >
            {t("loadingTitle")}
          </h2>
          {meta && (
            <span className="inline-flex h-6.5 items-center gap-1.5 rounded-full border border-[color-mix(in_oklab,var(--accent),var(--border)_55%)] bg-accent-soft px-2.5 text-label-sm font-bold text-text-2">
              <span
                aria-hidden
                className="h-1.5 w-1.5 rounded-full"
                style={{ background: meta.dot }}
              />
              {meta.name}
              {meta.version && ` ${meta.version}`}
            </span>
          )}
        </div>
        <Button
          variant="secondary"
          disabled
          title={t("copyWaiting")}
          className="h-10 gap-2 rounded-[var(--radius-md)] border-0 bg-text px-4 font-bold text-bg opacity-40"
        >
          <Copy size={16} />
          {t("copy")}
        </Button>
      </div>

      <ol role="status" aria-live="polite" className="m-0 flex flex-wrap gap-2 p-0">
        {STEPS.map((s, i) => {
          const done = i < active;
          const now = i === active;
          return (
            <li
              key={s.key}
              className={cn(
                "flex min-w-36 flex-1 items-center gap-2 rounded-[var(--radius-md)] border px-3 py-2.5 text-body-sm font-semibold",
                done &&
                  "border-[color-mix(in_oklab,var(--quality),var(--border)_60%)] bg-[color-mix(in_oklab,var(--quality),var(--surface)_88%)] text-quality",
                now &&
                  "border-[color-mix(in_oklab,var(--accent),var(--border)_45%)] bg-accent-soft text-text-2",
                !done && !now && "border-border bg-surface-2 text-subtle",
              )}
            >
              {done ? (
                <Check size={16} strokeWidth={2.4} />
              ) : now ? (
                <LoaderCircle size={16} strokeWidth={2.4} className="animate-spin" />
              ) : (
                <span
                  aria-hidden
                  className="h-4 w-4 rounded-full border-2 border-border-strong"
                />
              )}
              {t(done ? `step${s.key}Done` : `step${s.key}`)}
            </li>
          );
        })}
      </ol>

      <div className="flex flex-col gap-3.5 rounded-[var(--radius-lg)] border border-border bg-sunk p-5">
        {[92, 100, 84, 96, 58].map((w, i) => (
          <span
            key={i}
            aria-hidden
            className="h-3.5 animate-pulse rounded-[6px] bg-surface-2"
            style={{ width: `${w}%` }}
          />
        ))}
      </div>

      <div className="grid gap-2.5 sm:grid-cols-2">
        {[0, 1].map((i) => (
          <div
            key={i}
            className="flex flex-col gap-2.5 rounded-[var(--radius-lg)] border border-border bg-surface-2 p-4"
          >
            <span aria-hidden className="h-2.5 w-2/5 animate-pulse rounded bg-sunk" />
            <span aria-hidden className="h-3 w-11/12 animate-pulse rounded bg-sunk" />
            <span aria-hidden className="h-3 w-3/4 animate-pulse rounded bg-sunk" />
          </div>
        ))}
      </div>
    </section>
  );
}

/** Xato holati: sabab + qayta urinish. */
export function ErrorResult({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  const t = useTranslations("result");
  return (
    <section className={cn(panel, "items-center justify-center text-center")}>
      <div className="flex max-w-md flex-col items-center gap-4">
        <span className="flex h-16 w-16 items-center justify-center rounded-[18px] border border-error bg-error-soft text-error">
          <AlertTriangle size={28} strokeWidth={1.6} />
        </span>
        <h2 className="text-headline-sm font-extrabold text-text">{t("errorTitle")}</h2>
        <p className="text-body-md text-muted">{message}</p>
        <Button variant="secondary" className="h-11 px-5" onClick={onRetry}>
          {t("retry")}
        </Button>
      </div>
    </section>
  );
}
