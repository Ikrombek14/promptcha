"use client";

import { useTranslations } from "next-intl";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Stage } from "@/lib/draft";

const STAGES: Stage[] = ["classify", "clarify", "generate", "explain"];

type Props = { stage: Stage | null; compact?: boolean; className?: string };

/** Tahlil → Savollar → Prompt → Izohlar. Faol bosqich nuqtasi halqa bilan «nafas oladi». */
export function StageIndicator({ stage, compact, className }: Props) {
  const t = useTranslations("stages");
  const current = stage === "done" ? STAGES.length : stage ? STAGES.indexOf(stage) : -1;

  return (
    <ol
      aria-label={t("aria")}
      className={cn("flex items-center", compact ? "gap-2" : "gap-3", className)}
    >
      {STAGES.map((s, i) => {
        const state = i < current ? "done" : i === current ? "active" : "todo";
        return (
          <li key={s} className="flex items-center gap-2">
            {i > 0 && (
              <span
                aria-hidden
                className={cn(
                  "h-px transition-colors duration-300",
                  compact ? "w-4" : "w-8",
                  state === "todo" ? "bg-border" : "bg-accent",
                )}
              />
            )}
            <span
              aria-current={state === "active" ? "step" : undefined}
              className={cn(
                "relative flex shrink-0 items-center justify-center rounded-full border transition-colors duration-300",
                compact ? "h-3.5 w-3.5" : "h-5 w-5",
                state === "todo" && "border-border bg-surface",
                state === "active" && "stage-active border-accent bg-accent",
                state === "done" && "border-accent bg-accent text-on-accent",
              )}
            >
              {state === "done" && <Check size={compact ? 9 : 12} strokeWidth={3} />}
            </span>
            <span
              className={cn(
                "font-mono transition-colors duration-300",
                compact ? "text-code-sm" : "text-body-sm",
                state === "todo" ? "text-muted" : "text-text",
              )}
            >
              {t(s)}
            </span>
          </li>
        );
      })}
    </ol>
  );
}
