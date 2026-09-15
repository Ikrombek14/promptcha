"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { motion, useReducedMotion } from "motion/react";
import { Button } from "@/components/ui/button";
import { Chip } from "@/components/ui/chip";
import { Input } from "@/components/ui/textarea";
import type { ClarifyQuestion } from "@/lib/api";
import { fadeUp, stagger } from "@/lib/motion";

type Props = {
  questions: ClarifyQuestion[];
  onSubmit: (answers: Record<string, string>) => void;
  onSkip: () => void;
};

/** Bir savolga bir nechta chip + ixtiyoriy oʻz javobi; serverga vergul bilan birlashtirilib yuboriladi. */
type Pick = { chosen: string[]; custom: boolean; text: string };

const EMPTY: Pick = { chosen: [], custom: false, text: "" };

function toAnswer(p: Pick): string {
  const parts = [...p.chosen];
  if (p.custom && p.text.trim()) parts.push(p.text.trim());
  return parts.join(", ");
}

export function Step4Clarify({ questions, onSubmit, onSkip }: Props) {
  const t = useTranslations("clarify");
  const reduce = useReducedMotion();
  const [picks, setPicks] = useState<Record<string, Pick>>({});

  const pick = (id: string) => picks[id] ?? EMPTY;
  const update = (id: string, f: (p: Pick) => Pick) =>
    setPicks((all) => ({ ...all, [id]: f(all[id] ?? EMPTY) }));

  const answers = Object.fromEntries(
    questions.map((q) => [q.id, toAnswer(pick(q.id))]),
  );
  const allAnswered = questions.every((q) => answers[q.id].length > 0);
  const submit = () => {
    if (allAnswered) onSubmit(answers);
  };

  return (
    <motion.div
      className="flex flex-col gap-6"
      variants={stagger}
      initial={reduce ? false : "hidden"}
      animate="show"
    >
      <motion.div variants={fadeUp}>
        <h2 className="font-serif text-headline-md text-text">{t("title")}</h2>
        <p className="mt-1 text-body-md text-muted">{t("subtitle")}</p>
      </motion.div>

      {questions.map((q, i) => {
        const p = pick(q.id);
        return (
          <motion.fieldset
            key={q.id}
            variants={fadeUp}
            className="flex flex-col gap-3"
          >
            <legend className="text-body-md text-text">
              <span className="mr-2 font-mono text-code-sm text-accent">
                {i + 1}.
              </span>
              {q.question}
            </legend>
            <div
              className="flex flex-wrap gap-2"
              role="group"
              aria-label={q.question}
            >
              {q.options.map((opt) => {
                const on = p.chosen.includes(opt);
                return (
                  <Chip
                    key={opt}
                    selected={on}
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
                selected={p.custom}
                onClick={() =>
                  update(q.id, (cur) => ({ ...cur, custom: !cur.custom }))
                }
              >
                {t("custom")}
              </Chip>
            </div>
            {p.custom && (
              <Input
                autoFocus
                placeholder={t("customPlaceholder")}
                value={p.text}
                onChange={(e) =>
                  update(q.id, (cur) => ({ ...cur, text: e.target.value }))
                }
                onKeyDown={(e) => {
                  if (e.key === "Enter") submit();
                }}
              />
            )}
          </motion.fieldset>
        );
      })}

      <motion.div
        variants={fadeUp}
        className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"
      >
        <Button
          variant="primary"
          size="lg"
          disabled={!allAnswered}
          onClick={submit}
        >
          {t("continue")}
        </Button>
        <Button variant="ghost" onClick={onSkip}>
          {t("skip")}
        </Button>
      </motion.div>
    </motion.div>
  );
}
