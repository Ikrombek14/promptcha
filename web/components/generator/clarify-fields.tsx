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

/** Savollar roʻyxati: raqam, savol, chiplar va «Boshqa…» maydoni. Ramkasiz — kartani egasi beradi. */
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
      className="flex w-full flex-col gap-5"
      variants={stagger}
      initial="hidden"
      animate="show"
    >
      {questions.map((q, i) => {
        const p = pick(q.id);
        return (
          <motion.fieldset
            key={q.id}
            variants={fadeUp}
            className="flex min-w-0 flex-col gap-2.5"
          >
            <legend className="mb-2.5 flex gap-2 text-body-md font-bold text-text">
              <span className="font-mono text-body-sm text-accent">{i + 1}.</span>
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
                    className="h-10"
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
                className="h-10"
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
