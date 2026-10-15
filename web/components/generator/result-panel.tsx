"use client";

import { useState } from "react";
import { useLocale, useTranslations } from "next-intl";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import {
  Bookmark,
  Check,
  Copy,
  Languages,
  LoaderCircle,
  Plus,
  Sparkles,
  WandSparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScoreRing } from "@/components/generator/score-ring";
import {
  AI_META,
  type AiTool,
  type Kind,
  type Locale,
  wordCount,
} from "@/lib/ai-tools";
import {
  type PromptPart,
  type PromptSegment,
  translatePrompt,
} from "@/lib/api";
import { SLOT_OF, legendTypes, segClass, slotColor } from "@/lib/segments";
import { quickEdits } from "@/lib/quick-edits";
import { fadeUp, stagger } from "@/lib/motion";
import { cn } from "@/lib/utils";

/** Shu baldan past boʻlsa «Yaxshilash» taklif qilinadi */
const IMPROVE_BELOW = 75;

type Props = {
  ai: AiTool;
  kind: Kind | null;
  prompt: string;
  segments: PromptSegment[];
  parts: PromptPart[];
  notes: string[];
  score: number | null;
  streaming: boolean;
  /** Natija bazaga saqlangan boʻlsa — kutubxona tugmasi */
  promptId: string | null;
  saved: boolean;
  onSave: (saved: boolean) => void;
  /** «Yaxshilash» va tez oʻzgartirish — berilmasa tugmalar chiqmaydi */
  onImprove?: (feedback: string[]) => void;
};

export function ResultPanel({
  ai,
  kind,
  prompt,
  segments,
  parts,
  notes,
  score,
  streaming,
  promptId,
  saved,
  onSave,
  onImprove,
}: Props) {
  const t = useTranslations("result");
  const ts = useTranslations("segments");
  const tq = useTranslations("quick");
  const locale = useLocale() as Locale;
  const reduce = useReducedMotion();
  const meta = AI_META[ai];

  const [copied, setCopied] = useState(false);
  const [translated, setTranslated] = useState<{ text: string; of: string } | null>(null);
  const [translating, setTranslating] = useState(false);
  const [translateError, setTranslateError] = useState<string | null>(null);
  const showUz = translated !== null && translated.of === prompt;

  const copy = async () => {
    try {
      // Nusxa olganda har doim inglizcha asl matn (AI'lar unga yaxshiroq javob beradi)
      await navigator.clipboard.writeText(prompt);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      /* clipboard yoʻq */
    }
  };

  const toggleTranslate = async () => {
    if (showUz) {
      setTranslated(null);
      return;
    }
    setTranslateError(null);
    setTranslating(true);
    try {
      setTranslated({ text: await translatePrompt(prompt, locale), of: prompt });
    } catch {
      setTranslateError(t("translateError"));
    } finally {
      setTranslating(false);
    }
  };

  const legend = legendTypes(kind);
  const words = wordCount(prompt);
  const useSegments = !streaming && segments.length > 0;

  return (
    <motion.section
      aria-labelledby="h-out"
      className="flex min-w-0 flex-col gap-6 rounded-[var(--radius-xl)] border border-border bg-surface p-5 md:p-7"
      variants={stagger}
      initial={reduce ? false : "hidden"}
      animate="show"
    >
      {/* Sarlavha + model + sifat */}
      <motion.div variants={fadeUp} className="flex flex-wrap items-center gap-4">
        <div className="flex min-w-60 flex-1 flex-col gap-1.5">
          <div className="flex flex-wrap items-center gap-2.5">
            <h2
              id="h-out"
              className="text-headline-sm font-extrabold tracking-[-0.02em] text-text md:text-headline-md"
            >
              {streaming ? t("loadingTitle") : t("title")}
            </h2>
            <span className="inline-flex h-6.5 items-center gap-1.5 rounded-full border border-[color-mix(in_oklab,var(--accent),var(--border)_55%)] bg-accent-soft px-2.5 text-label-sm font-bold text-text-2">
              <span
                aria-hidden
                className="h-1.5 w-1.5 rounded-full"
                style={{ background: meta.dot }}
              />
              {meta.name}
              {meta.version && ` ${meta.version}`}
            </span>
          </div>
          {!streaming && <p className="text-body-sm text-muted">{t("subtitle")}</p>}
        </div>
        {score !== null && <ScoreRing score={score} />}
      </motion.div>

      {/* Til + saqlash + nusxa */}
      <motion.div
        variants={fadeUp}
        className="flex flex-wrap items-center justify-between gap-3"
      >
        {locale === "en" || streaming ? (
          <span />
        ) : (
          <div
            role="group"
            aria-label={t("translate")}
            className="flex gap-0.5 rounded-[var(--radius-md)] border border-border bg-sunk p-0.5"
          >
            <button
              type="button"
              aria-pressed={!showUz}
              onClick={() => setTranslated(null)}
              className={cn(
                "h-9 rounded-[7px] px-3.5 text-body-sm font-bold transition-colors",
                !showUz ? "bg-surface-2 text-text" : "text-muted hover:text-text",
              )}
            >
              {t("viewOriginal")}
            </button>
            <button
              type="button"
              aria-pressed={showUz}
              disabled={translating}
              onClick={() => void toggleTranslate()}
              className={cn(
                "flex h-9 items-center gap-1.5 rounded-[7px] px-3.5 text-body-sm font-bold transition-colors disabled:opacity-60",
                showUz ? "bg-surface-2 text-text" : "text-muted hover:text-text",
              )}
            >
              {translating ? (
                <LoaderCircle size={14} className="animate-spin" />
              ) : (
                <Languages size={14} />
              )}
              {t("viewTranslated")}
            </button>
          </div>
        )}

        <div className="flex gap-2">
          {promptId && (
            <Button
              variant="secondary"
              size="icon"
              aria-label={saved ? t("unsave") : t("save")}
              title={saved ? t("unsave") : t("save")}
              aria-pressed={saved}
              className={cn(
                "h-10 w-10 rounded-[var(--radius-md)]",
                saved && "border-selected-border text-accent",
              )}
              onClick={() => onSave(!saved)}
            >
              <Bookmark size={16} fill={saved ? "currentColor" : "none"} />
            </Button>
          )}
          <Button
            variant="secondary"
            disabled={streaming || !prompt}
            title={streaming ? t("copyWaiting") : undefined}
            className="h-10 gap-2 rounded-[var(--radius-md)] border-0 bg-text px-4 font-bold text-bg hover:bg-text-2 disabled:opacity-40"
            onClick={() => void copy()}
          >
            {copied ? <Check size={16} strokeWidth={2.4} /> : <Copy size={16} />}
            <span aria-live="polite">{copied ? t("copied") : t("copy")}</span>
          </Button>
        </div>
      </motion.div>

      {/* Prompt bloki */}
      <motion.div
        variants={fadeUp}
        className="overflow-hidden rounded-[var(--radius-lg)] border border-border bg-sunk"
      >
        {useSegments && !showUz && (
          <div className="flex flex-wrap gap-4 border-b border-border px-5 py-3 text-label-sm font-semibold text-muted">
            {legend.map((type) => (
              <span key={type} className="flex items-center gap-1.5">
                <span
                  aria-hidden
                  className="h-2 w-2 rounded-[2px]"
                  style={{ background: slotColor(type) }}
                />
                {ts(type)}
              </span>
            ))}
          </div>
        )}

        {showUz ? (
          <div className="flex flex-col gap-3 px-5 py-5">
            <p className="whitespace-pre-wrap text-body-md leading-[1.8] text-text-2">
              {translated.text}
            </p>
            <p className="text-body-sm text-subtle">{t("translateNote")}</p>
          </div>
        ) : (
          <p className="whitespace-pre-wrap px-5 py-5 font-mono text-code-md leading-[1.85] text-text-2">
            {useSegments
              ? segments.map((sg, i) => {
                  const cls = segClass(sg.type);
                  return cls ? (
                    <span key={i} className={cls}>
                      {sg.text}
                    </span>
                  ) : (
                    <span key={i}>{sg.text}</span>
                  );
                })
              : prompt}
            {streaming && (
              <span
                aria-hidden
                className="animate-caret ml-0.5 inline-block h-4 w-[2px] translate-y-0.5 bg-accent"
              />
            )}
          </p>
        )}

        {!streaming && (
          <div className="flex flex-wrap justify-between gap-3 border-t border-border px-5 py-2.5 font-mono text-label-sm text-subtle">
            <span>{t("wordsChars", { w: words, c: prompt.length })}</span>
            <span>{t("syntax", { ai: meta.name })}</span>
          </div>
        )}
      </motion.div>

      {translateError && <p className="text-body-sm text-error">{translateError}</p>}

      {/* Prompt anatomiyasi */}
      {parts.length > 0 && (
        <motion.div variants={fadeUp} className="flex flex-col gap-3">
          <div className="flex items-baseline justify-between gap-3">
            <h3 className="text-body-lg font-extrabold tracking-[-0.01em] text-text">
              {t("anatomy")}
            </h3>
            <span className="text-body-sm text-subtle">
              {t("anatomyCount", { n: parts.length })}
            </span>
          </div>
          <div className="grid gap-2.5 sm:grid-cols-2">
            {parts.map((p, i) => (
              <article
                key={`${p.type}-${i}`}
                className="flex min-w-0 flex-col gap-2 rounded-[var(--radius-lg)] border border-border bg-surface-2 p-4"
              >
                <span className="flex items-center gap-2 text-label-sm font-bold uppercase tracking-wider">
                  <span
                    aria-hidden
                    className="h-2 w-2 rounded-[2px]"
                    style={{ background: slotColor(p.type) }}
                  />
                  <span style={{ color: slotColor(p.type) }}>
                    {p.type in SLOT_OF ? ts(p.type) : p.type}
                  </span>
                </span>
                <span className="truncate font-mono text-code-sm text-text-2">
                  {p.excerpt}
                </span>
                <p className="text-body-sm text-muted">{p.why}</p>
              </article>
            ))}
          </div>
        </motion.div>
      )}

      {/* Izohlar (anatomiya boʻlmasa — pipeline izohlari) */}
      {parts.length === 0 && notes.length > 0 && !streaming && (
        <motion.ul variants={fadeUp} className="flex flex-col gap-2">
          {notes.map((n, i) => (
            <li
              key={i}
              className="flex gap-2.5 rounded-[var(--radius-lg)] border border-border bg-surface-2 p-3.5 text-body-sm text-muted"
            >
              <Sparkles size={15} className="mt-0.5 shrink-0 text-accent" />
              {n}
            </li>
          ))}
        </motion.ul>
      )}

      {/* Tez oʻzgartirish + yaxshilash */}
      {onImprove && !streaming && prompt && (
        <motion.div variants={fadeUp} className="flex flex-col gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="mr-1 text-body-sm font-bold text-text-2">{t("quick")}</span>
            {quickEdits(kind).map((q) => (
              <button
                key={q.id}
                type="button"
                onClick={() => onImprove([q.instruction])}
                className="flex h-9 items-center gap-1.5 rounded-full border border-border-strong px-3 text-body-sm font-semibold text-muted transition-colors hover:border-[color-mix(in_oklab,var(--border-strong),var(--text)_30%)] hover:text-text"
              >
                <Plus size={14} strokeWidth={2} />
                {tq(q.id)}
              </button>
            ))}
          </div>
          <AnimatePresence initial={false}>
            {score !== null && score < IMPROVE_BELOW && (
              <motion.div
                key="improve"
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="flex flex-wrap items-center justify-between gap-3 rounded-[var(--radius-lg)] border border-border bg-surface-2 p-3.5"
              >
                <p className="text-body-sm text-muted">{t("improveHint")}</p>
                <Button
                  variant="primary"
                  size="sm"
                  className="h-10 gap-2"
                  onClick={() => onImprove([])}
                >
                  <WandSparkles size={15} />
                  {t("improve")}
                </Button>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      )}
    </motion.section>
  );
}
