"use client";

import { useCallback, useState } from "react";
import { useTranslations } from "next-intl";
import { AnimatePresence, motion } from "motion/react";
import { Check, ThumbsDown, ThumbsUp, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/textarea";
import { type PendingFeedback, sendFeedback } from "@/lib/api";
import { track } from "@/lib/events";
import { cn } from "@/lib/utils";

/**
 * «Kecha yozgan promptingiz ishladimi?» — natija panelining tepasida bir marta.
 * Javob `prompts.feedback` ga va `prompt_feedback` hodisasiga yoziladi.
 */
export function FeedbackCard({
  item,
  onDone,
}: {
  item: PendingFeedback;
  onDone: () => void;
}) {
  const t = useTranslations("feedback");
  const [asking, setAsking] = useState<"not_worked" | null>(null);
  const [note, setNote] = useState("");
  const [sent, setSent] = useState(false);

  const answer = useCallback(
    (value: "worked" | "not_worked", text?: string) => {
      track("prompt_feedback", { prompt_id: item.id, answer: value });
      setSent(true);
      sendFeedback(item.id, value, text).catch(() => {});
      setTimeout(onDone, 1400);
    },
    [item.id, onDone],
  );

  return (
    <AnimatePresence>
      <motion.section
        key="feedback"
        aria-label={t("title")}
        initial={{ opacity: 0, y: -6 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, height: 0 }}
        className={cn(
          "flex flex-wrap items-center gap-3 rounded-[var(--radius-lg)] border p-3.5",
          sent
            ? "border-[color-mix(in_oklab,var(--quality),var(--border)_55%)] bg-[color-mix(in_oklab,var(--quality),var(--surface)_88%)]"
            : "border-border-strong bg-surface-2",
        )}
      >
        {sent ? (
          <p className="flex items-center gap-2 text-body-sm font-semibold text-quality">
            <Check size={16} strokeWidth={2.4} />
            {t("thanks")}
          </p>
        ) : asking === "not_worked" ? (
          <>
            <p className="min-w-40 flex-1 text-body-sm text-text-2">{t("whyLabel")}</p>
            <Input
              autoFocus
              value={note}
              placeholder={t("whyPlaceholder")}
              onChange={(e) => setNote(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") answer("not_worked", note);
              }}
              className="h-10 flex-[2]"
            />
            <Button variant="secondary" className="h-10" onClick={() => answer("not_worked", note)}>
              {t("send")}
            </Button>
          </>
        ) : (
          <>
            <div className="flex min-w-48 flex-1 flex-col gap-0.5">
              <span className="text-body-sm font-bold text-text">{t("title")}</span>
              <span className="truncate text-label-sm text-muted">
                {item.input_text}
                {item.score !== null && ` · ${item.score}`}
              </span>
            </div>
            <Button variant="secondary" className="h-10 gap-2" onClick={() => answer("worked")}>
              <ThumbsUp size={15} />
              {t("worked")}
            </Button>
            <Button
              variant="secondary"
              className="h-10 gap-2"
              onClick={() => setAsking("not_worked")}
            >
              <ThumbsDown size={15} />
              {t("notWorked")}
            </Button>
            <Button
              variant="ghost"
              size="icon"
              aria-label={t("close")}
              className="h-10 w-10"
              onClick={onDone}
            >
              <X size={16} />
            </Button>
          </>
        )}
      </motion.section>
    </AnimatePresence>
  );
}
