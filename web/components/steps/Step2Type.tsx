"use client";

import { useTranslations } from "next-intl";
import { AnimatePresence, LayoutGroup, motion } from "motion/react";
import { Chip } from "@/components/ui/chip";
import { Label } from "@/components/ui/callout";
import { KINDS, type Kind } from "@/lib/ai-tools";
import { swap } from "@/lib/motion";

type Props = {
  value: Kind | null;
  onChange: (k: Kind | null) => void;
  /** Tahlil aniqlagan tur — «Avto» chipida koʻrsatiladi */
  suggested?: Kind | null;
  disabled?: boolean;
};

export function Step2Type({ value, onChange, suggested, disabled }: Props) {
  const t = useTranslations("app");
  const autoLabel = suggested && value === null ? suggested : null;
  return (
    <div className="flex flex-col gap-2">
      <Label>{t("kindLabel")}</Label>
      <LayoutGroup id="kind">
        <div className="flex flex-wrap gap-2">
          <Chip
            indicatorId="kind-indicator"
            selected={value === null}
            disabled={disabled}
            onClick={() => onChange(null)}
          >
            <AnimatePresence mode="wait" initial={false}>
              <motion.span key={autoLabel ?? "auto"} {...swap}>
                {autoLabel
                  ? t("kindAutoResolved", { kind: t(`kinds.${autoLabel}`) })
                  : t("kindAuto")}
              </motion.span>
            </AnimatePresence>
          </Chip>
          {KINDS.map((k) => (
            <Chip
              key={k}
              indicatorId="kind-indicator"
              selected={value === k}
              disabled={disabled}
              onClick={() => onChange(k)}
            >
              {t(`kinds.${k}`)}
            </Chip>
          ))}
        </div>
      </LayoutGroup>
    </div>
  );
}
