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

export function Step4Clarify({ questions, onSubmit, onSkip }: Props) {
  const t = useTranslations("clarify");
  const reduce = useReducedMotion();
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [custom, setCustom] = useState<Record<string, boolean>>({});

  const allAnswered = questions.every((q) => (answers[q.id] ?? "").trim().length > 0);

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

      {questions.map((q, i) => (
        <motion.fieldset key={q.id} variants={fadeUp} className="flex flex-col gap-3">
          <legend className="text-body-md text-text">
            <span className="mr-2 font-mono text-code-sm text-accent">{i + 1}.</span>
            {q.question}
          </legend>
          <div className="flex flex-wrap gap-2">
            {q.options.map((opt) => (
              <Chip
                key={opt}
                selected={!custom[q.id] && answers[q.id] === opt}
                onClick={() => {
                  setCustom((c) => ({ ...c, [q.id]: false }));
                  setAnswers((a) => ({ ...a, [q.id]: opt }));
                }}
              >
                {opt}
              </Chip>
            ))}
            <Chip
              selected={!!custom[q.id]}
              onClick={() => {
                setCustom((c) => ({ ...c, [q.id]: true }));
                setAnswers((a) => ({ ...a, [q.id]: "" }));
              }}
            >
              {t("custom")}
            </Chip>
          </div>
          {custom[q.id] && (
            <Input
              autoFocus
              placeholder={t("customPlaceholder")}
              value={answers[q.id] ?? ""}
              onChange={(e) => setAnswers((a) => ({ ...a, [q.id]: e.target.value }))}
              onKeyDown={(e) => {
                if (e.key === "Enter" && allAnswered) onSubmit(answers);
              }}
            />
          )}
        </motion.fieldset>
      ))}

      <motion.div
        variants={fadeUp}
        className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"
      >
        <Button variant="primary" size="lg" disabled={!allAnswered} onClick={() => onSubmit(answers)}>
          {t("continue")}
        </Button>
        <Button variant="ghost" onClick={onSkip}>
          {t("skip")}
        </Button>
      </motion.div>
    </motion.div>
  );
}
