"use client";

import { useEffect, useState } from "react";
import { useLocale, useTranslations } from "next-intl";
import {
  AnimatePresence,
  LayoutGroup,
  motion,
  useReducedMotion,
} from "motion/react";
import {
  Check,
  Copy,
  HelpCircle,
  Languages,
  SlidersHorizontal,
  Wand2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/callout";
import { StageIndicator } from "@/components/stage-indicator";
import {
  AI_META,
  type AiTool,
  type Kind,
  type Locale,
  familyFor,
  wordCount,
} from "@/lib/ai-tools";
import {
  type ClarifyQuestion,
  type ReviewCriterion,
  translatePrompt,
} from "@/lib/api";
import type { Stage } from "@/lib/draft";
import { fadeUp, springPop, stagger } from "@/lib/motion";
import { cn } from "@/lib/utils";

const REVEAL_MS = 1100;
/** Shu baldan past boʻlsa «Yaxshilash» taklif qilinadi */
const IMPROVE_BELOW = 75;

function scoreTone(score: number): string {
  if (score >= 80) return "border-accent text-accent";
  if (score >= 60) return "border-border text-text";
  return "border-error text-error";
}

type Props = {
  ai: AiTool;
  kind: Kind | null;
  /** Foydalanuvchi vositani oʻzi tanlamagan — sayt aniqlagan */
  auto: boolean;
  prompt: string;
  notes: string[];
  streaming: boolean;
  stage: Stage | null;
  /** Ish hozirgina jonli tugadi — vosita «ochilish» animatsiyasi bilan koʻrsatiladi */
  reveal: boolean;
  questions: ClarifyQuestion[];
  answers: Record<string, string>;
  /** Tekshiruv bali (0–100); null — hali kelmagan */
  score: number | null;
  criteria: ReviewCriterion[];
  /** «Yaxshilash» — berilmasa tugma chiqmaydi (yasalmoqda, limit tugagan) */
  onImprove?: () => void;
};

/** "«...» — sabab" koʻrinishidagi izohni sarlavha va tanaga ajratadi. */
function splitNote(note: string): { head: string; body: string } {
  const m = note.match(/^([\s\S]{3,80}?)\s+[—–-]\s+([\s\S]+)$/);
  return m ? { head: m[1], body: m[2] } : { head: "", body: note };
}

export function Step5Result({
  ai,
  kind,
  auto,
  prompt,
  notes,
  streaming,
  stage,
  reveal,
  questions,
  answers,
  score,
  criteria,
  onImprove,
}: Props) {
  const t = useTranslations("result");
  const tf = useTranslations("families");
  const locale = useLocale() as Locale;
  const reduce = useReducedMotion();
  const [copied, setCopied] = useState(false);
  const [showNotes, setShowNotes] = useState(true);
  const [revealing, setRevealing] = useState(reveal && !reduce);
  // Tarjima: prompt inglizcha qoladi (AI'lar shunga yaxshi javob beradi), tarjima faqat oʻqish uchun
  const [translation, setTranslation] = useState<{
    text: string;
    forPrompt: string;
  } | null>(null);
  const [translating, setTranslating] = useState(false);
  const [translateError, setTranslateError] = useState<string | null>(null);
  const meta = AI_META[ai];
  const showTranslation =
    translation !== null && translation.forPrompt === prompt;

  const toggleTranslation = async () => {
    if (showTranslation) {
      setTranslation(null);
      return;
    }
    setTranslateError(null);
    setTranslating(true);
    try {
      const text = await translatePrompt(prompt, locale);
      setTranslation({ text, forPrompt: prompt });
    } catch {
      setTranslateError(t("translateError"));
    } finally {
      setTranslating(false);
    }
  };

  useEffect(() => {
    if (!revealing) return;
    const id = setTimeout(() => setRevealing(false), REVEAL_MS);
    return () => clearTimeout(id);
  }, [revealing]);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(prompt);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard yoʻq */
    }
  };

  const answered = questions
    .map((q) => ({ q: q.question, a: answers[q.id] }))
    .filter((x) => x.a && x.a.trim() && x.a !== "(not specified)");

  return (
    <LayoutGroup id="result">
      <AnimatePresence mode="wait" initial={false}>
        {revealing ? (
          <motion.div
            key="reveal"
            className="flex flex-1 flex-col items-center justify-center gap-4 text-center"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, transition: { duration: 0.15 } }}
          >
            <motion.p
              className="text-label-sm font-medium uppercase tracking-wider text-muted"
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0, transition: { delay: 0.35 } }}
            >
              {auto ? t("chosenAuto") : t("chosenTool")}
            </motion.p>
            <motion.div
              layoutId="ai-badge"
              className="flex items-center gap-3 rounded-[var(--radius)] border border-border bg-surface-2 px-5 py-3"
            >
              <motion.span
                aria-hidden
                className="h-4 w-4 shrink-0 rounded-full"
                style={{ background: meta.dot }}
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ ...springPop, delay: 0.1 }}
              />
              <motion.span
                className="font-serif text-headline-md text-text"
                initial={{ opacity: 0, x: -6 }}
                animate={{
                  opacity: 1,
                  x: 0,
                  transition: { delay: 0.25, duration: 0.3 },
                }}
              >
                {meta.name}
              </motion.span>
              <motion.span
                className="rounded-[var(--radius-sm)] border border-border bg-surface px-2 py-0.5 font-mono text-code-sm text-muted"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1, transition: { delay: 0.5 } }}
              >
                {meta.version || tf(familyFor(ai, kind))}
              </motion.span>
            </motion.div>
          </motion.div>
        ) : (
          <motion.div
            key="content"
            className="flex flex-col gap-5"
            variants={stagger}
            initial={reveal && !reduce ? "hidden" : false}
            animate="show"
          >
            <motion.div
              variants={fadeUp}
              className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-3"
            >
              <div className="flex flex-wrap items-center gap-3">
                <h2 className="font-serif text-headline-md text-text">
                  {streaming ? t("writing") : t("title")}
                </h2>
                <motion.div
                  layoutId="ai-badge"
                  className="inline-flex items-center gap-2 rounded-[var(--radius-sm)] border border-border bg-surface-2 px-2 py-0.5 font-mono text-code-sm text-muted"
                >
                  <span
                    aria-hidden
                    className="h-2 w-2 rounded-full"
                    style={{ background: meta.dot }}
                  />
                  <span className="text-text">{meta.name}</span>
                  {meta.version && <span>{meta.version}</span>}
                </motion.div>
                {score !== null && !streaming && (
                  <motion.span
                    key={score}
                    role="status"
                    aria-label={t("scoreAria")}
                    className={cn(
                      "inline-flex items-center rounded-[var(--radius-sm)] border bg-surface px-2 py-0.5 font-mono text-code-sm tabular-nums",
                      scoreTone(score),
                    )}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.2 }}
                  >
                    {t("score", { n: score })}
                  </motion.span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  aria-pressed={showNotes}
                  disabled={!notes.length}
                  onClick={() => setShowNotes((s) => !s)}
                >
                  <HelpCircle size={16} />
                  {t("why")}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  aria-pressed={showTranslation}
                  disabled={streaming || !prompt || translating}
                  onClick={() => void toggleTranslation()}
                >
                  <Languages size={16} />
                  {translating ? t("translating") : t("translate")}
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={streaming || !prompt}
                  onClick={copy}
                >
                  <AnimatePresence mode="wait" initial={false}>
                    <motion.span
                      key={copied ? "ok" : "copy"}
                      className="inline-flex items-center gap-2"
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.8 }}
                      transition={{ duration: 0.15 }}
                    >
                      {copied ? <Check size={16} /> : <Copy size={16} />}
                      {copied ? t("copied") : t("copy")}
                    </motion.span>
                  </AnimatePresence>
                </Button>
              </div>
            </motion.div>

            {streaming && <StageIndicator stage={stage} compact />}

            <motion.div variants={fadeUp} className="flex flex-col gap-2">
              <div className="flex items-center justify-between font-mono text-code-sm text-muted">
                <span>{t("format", { format: tf(familyFor(ai, kind)) })}</span>
                <span>{t("words", { n: wordCount(prompt) })}</span>
              </div>
              <pre
                aria-live="polite"
                className="whitespace-pre-wrap break-words rounded-[var(--radius)] border border-border bg-surface-2 p-4 font-mono text-code-md text-text"
              >
                {prompt}
                {streaming && (
                  <span
                    aria-hidden
                    className="animate-caret ml-0.5 inline-block h-4 w-2 bg-accent align-middle"
                  />
                )}
              </pre>
            </motion.div>

            <AnimatePresence initial={false}>
              {showTranslation && (
                <motion.div
                  key="translation"
                  className="flex flex-col gap-2"
                  initial={reduce ? false : { opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -6 }}
                  transition={{ duration: 0.2 }}
                >
                  <div className="flex items-center justify-between">
                    <Label>{t("translated")}</Label>
                    <span className="font-mono text-code-sm text-muted">
                      {tf(familyFor(ai, kind))}
                    </span>
                  </div>
                  <p className="whitespace-pre-wrap break-words rounded-[var(--radius)] border border-border border-l-2 border-l-accent bg-surface p-4 text-body-md text-text">
                    {translation.text}
                  </p>
                  <p className="text-body-sm text-muted">
                    {t("translateHint")}
                  </p>
                </motion.div>
              )}
            </AnimatePresence>

            {translateError && (
              <p role="alert" className="text-body-sm text-error">
                {translateError}
              </p>
            )}

            {notes.length > 0 && showNotes && (
              <motion.section
                variants={stagger}
                className="flex flex-col gap-3"
              >
                <motion.div
                  variants={fadeUp}
                  className="flex items-center justify-between"
                >
                  <Label>{t("notesLabel")}</Label>
                  <span className="font-mono text-code-sm text-muted">
                    {t("notesCount", { n: notes.length })}
                  </span>
                </motion.div>
                {notes.map((n, i) => {
                  const { head, body } = splitNote(n);
                  return (
                    <motion.div
                      key={i}
                      variants={fadeUp}
                      className="rounded-[var(--radius-sm)] border border-border border-l-2 border-l-accent bg-surface-2 p-3"
                    >
                      {head && (
                        <p className="mb-0.5 font-mono text-code-sm font-medium text-accent">
                          {i + 1}. {head}
                        </p>
                      )}
                      <p className="text-body-md text-text">{body}</p>
                    </motion.div>
                  );
                })}
              </motion.section>
            )}

            {score !== null &&
              score < IMPROVE_BELOW &&
              !streaming &&
              onImprove && (
                <motion.div
                  variants={fadeUp}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-[var(--radius-sm)] border border-border bg-surface-2 p-3"
                >
                  <div className="flex flex-col gap-1">
                    <p className="text-body-md text-text">{t("improveHint")}</p>
                    {criteria.some((c) => !c.ok && c.note) && (
                      <ul className="flex flex-col gap-0.5 text-body-sm text-muted">
                        {criteria
                          .filter((c) => !c.ok && c.note)
                          .map((c) => (
                            <li key={c.name}>· {c.note}</li>
                          ))}
                      </ul>
                    )}
                  </div>
                  <Button variant="secondary" size="sm" onClick={onImprove}>
                    <Wand2 size={16} />
                    {t("improve")}
                  </Button>
                </motion.div>
              )}

            {answered.length > 0 && (
              <motion.section
                variants={stagger}
                className="flex flex-col gap-2"
              >
                <motion.div variants={fadeUp}>
                  <Label className="flex items-center gap-2">
                    <SlidersHorizontal size={14} />
                    {t("answersLabel")}
                  </Label>
                </motion.div>
                {answered.map((x, i) => (
                  <motion.div
                    key={i}
                    variants={fadeUp}
                    className="flex items-center justify-between gap-3 rounded-[var(--radius-sm)] border border-border bg-surface-2 px-3 py-2 text-body-md"
                  >
                    <span className="text-text">{x.q}</span>
                    <span className="shrink-0 text-muted">{x.a}</span>
                  </motion.div>
                ))}
              </motion.section>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </LayoutGroup>
  );
}
