"use client";

import { useTranslations } from "next-intl";
import { motion } from "motion/react";
import { Chip } from "@/components/ui/chip";
import { Input } from "@/components/ui/textarea";
import type { ClarifyQuestion } from "@/lib/api";
import { fadeUp, stagger } from "@/lib/motion";

/** Bir savolga bir nechta chip + ixtiyoriy oʻz javobi. */
export type Pick = { chosen: string[]; custom: boolean; text: string };

export const EMPTY_PICK: Pick = { chosen: [], custom: false, text: "" };

/** Tanlovlarni serverga ketadigan javobga aylantiradi (vergul bilan). */
export function toAnswers(
  questions: ClarifyQuestion[],
  picks: Record<string, Pick>,
): Record<string, string> {
  const out: Record<string, string> = {};
  for (const q of questions) {
    const p = picks[q.id] ?? EMPTY_PICK;
    const parts = [...p.chosen];
    if (p.custom && p.text.trim()) parts.push(p.text.trim());
    if (parts.length) out[q.id] = parts.join(", ");
  }
  return out;
}

type Props = {
  questions: ClarifyQuestion[];
  picks: Record<string, Pick>;
  onChange: (picks: Record<string, Pick>) => void;
  onSubmit: () => void;
  disabled?: boolean;
};

/**
 * Aniqlashtiruvchi savollar — gʻoya maydoni ostida, ixtiyoriy.
 * Javob bermasa ham prompt yasaladi (asosiy tugma bitta).
 */
export function ClarifyFields({
  questions,
  picks,
  onChange,
  onSubmit,
  disabled,
}: Props) {
  const t = useTranslations("clarify");
  if (!questions.length) return null;

  const pick = (id: string) => picks[id] ?? EMPTY_PICK;
  const update = (id: string, f: (p: Pick) => Pick) =>
    onChange({ ...picks, [id]: f(pick(id)) });

  return (
    <motion.div
      className="flex flex-col gap-4 rounded-[var(--radius-lg)] border border-dashed border-border-strong bg-surface-2/60 p-4"
      variants={stagger}
      initial="hidden"
      animate="show"
    >
      <motion.p variants={fadeUp} className="text-body-sm text-muted">
        {t("subtitle")}
      </motion.p>

      {questions.map((q) => {
        const p = pick(q.id);
        return (
          <motion.fieldset
            key={q.id}
            variants={fadeUp}
            className="flex min-w-0 flex-col gap-2"
          >
            <legend className="mb-2 text-body-sm font-bold text-text-2">
              {q.question}
            </legend>
            <div className="flex flex-wrap gap-2" role="group" aria-label={q.question}>
              {q.options.map((opt) => {
                const on = p.chosen.includes(opt);
                return (
                  <Chip
                    key={opt}
                    tone="outline"
                    selected={on}
                    disabled={disabled}
                    onClick={() =>
                      update(q.id, (cur) => ({
                        ...cur,
                        chosen: on
                          ? cur.chosen.filter((o) => o !== opt)
                          : [...cur.chosen, opt],
                      }))
                    }
                  >
                    {opt}
                  </Chip>
                );
              })}
              <Chip
                tone="outline"
                selected={p.custom}
                disabled={disabled}
                onClick={() => update(q.id, (cur) => ({ ...cur, custom: !cur.custom }))}
              >
                {t("custom")}
              </Chip>
            </div>
            {p.custom && (
              <Input
                autoFocus
                placeholder={t("customPlaceholder")}
                value={p.text}
                disabled={disabled}
                onChange={(e) => update(q.id, (cur) => ({ ...cur, text: e.target.value }))}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    onSubmit();
                  }
                }}
              />
            )}
          </motion.fieldset>
        );
      })}
    </motion.div>
  );
}
