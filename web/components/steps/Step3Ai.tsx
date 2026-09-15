"use client";

import { useTranslations } from "next-intl";
import { AnimatePresence, LayoutGroup, motion } from "motion/react";
import { Chip } from "@/components/ui/chip";
import { AI_META, type AiTool, type Kind, familyFor } from "@/lib/ai-tools";
import { fadeUp, stagger } from "@/lib/motion";

type Props = {
  /** Tahlil tavsiya qilgan 2–3 vosita, birinchisi eng mosi */
  tools: AiTool[];
  kind: Kind | null;
  value: AiTool | null;
  onChange: (a: AiTool) => void;
  analyzing?: boolean;
  disabled?: boolean;
};

/** Tavsiya qilingan vositalar: yorliqsiz, faqat 2–3 chip; tahlil paytida skeleton. */
export function Step3Ai({
  tools,
  kind,
  value,
  onChange,
  analyzing,
  disabled,
}: Props) {
  const t = useTranslations("tools");
  const tf = useTranslations("families");

  return (
    <div className="flex flex-col gap-2">
      <AnimatePresence mode="wait" initial={false}>
        {analyzing || !tools.length ? (
          <motion.div
            key="skeleton"
            className="flex flex-col gap-2"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, transition: { duration: 0.15 } }}
            aria-busy
          >
            <p className="font-mono text-code-sm text-muted">
              {t("analyzing")}
            </p>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="h-10 animate-pulse rounded-[var(--radius-sm)] border border-border bg-surface-2"
                  style={{ animationDelay: `${i * 120}ms` }}
                />
              ))}
            </div>
          </motion.div>
        ) : (
          <motion.div
            key={tools.join(",")}
            variants={stagger}
            initial="hidden"
            animate="show"
            exit={{ opacity: 0, transition: { duration: 0.15 } }}
          >
            <LayoutGroup id="ai">
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                {tools.map((a, i) => (
                  <motion.div key={a} variants={fadeUp}>
                    <Chip
                      tone="outline"
                      indicatorId="ai-indicator"
                      dot={AI_META[a].dot}
                      selected={value === a}
                      disabled={disabled}
                      onClick={() => onChange(a)}
                      className="h-10 w-full justify-start px-3"
                      title={i === 0 ? t("bestFit") : undefined}
                    >
                      <span className="truncate">{AI_META[a].name}</span>
                      <span className="truncate font-mono text-code-sm font-normal text-muted">
                        {tf(familyFor(a, kind))}
                      </span>
                    </Chip>
                  </motion.div>
                ))}
              </div>
            </LayoutGroup>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
