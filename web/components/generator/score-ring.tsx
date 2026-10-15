"use client";

import { useTranslations } from "next-intl";
import { motion, useReducedMotion } from "motion/react";

const R = 17;
const C = 2 * Math.PI * R; // ≈ 106.8

/** Sifat bali: 0–100 halqa + daraja nomi. `compact` — mobil koʻrinish. */
export function ScoreRing({
  score,
  compact = false,
}: {
  score: number;
  compact?: boolean;
}) {
  const t = useTranslations("result");
  const reduce = useReducedMotion();
  const pct = Math.max(0, Math.min(100, score)) / 100;
  const color =
    score >= 85 ? "var(--quality)" : score >= 70 ? "var(--seg-light)" : "var(--error)";
  const label =
    score >= 85 ? t("scoreExcellent") : score >= 70 ? t("scoreGood") : t("scoreWeak");
  const size = compact ? 30 : 40;
  const r = compact ? 12.5 : R;
  const circ = 2 * Math.PI * r;

  return (
    <div
      className="flex items-center gap-2.5 rounded-full border border-border bg-surface-2 py-1.5 pl-1.5 pr-3.5"
      title={t("score", { n: score })}
    >
      <span
        className="relative flex items-center justify-center"
        style={{ width: size, height: size }}
      >
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          aria-hidden
          className="absolute inset-0 -rotate-90"
        >
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke="var(--border-strong)"
            strokeWidth={compact ? 3 : 3.5}
          />
          <motion.circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={color}
            strokeWidth={compact ? 3 : 3.5}
            strokeLinecap="round"
            strokeDasharray={circ}
            initial={reduce ? false : { strokeDashoffset: circ }}
            animate={{ strokeDashoffset: circ * (1 - pct) }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          />
        </svg>
        <span className="text-label-sm font-extrabold text-text">{score}</span>
      </span>
      {compact ? (
        <span className="text-label-sm font-bold text-text">{label}</span>
      ) : (
        <span className="flex flex-col leading-tight">
          <span className="text-body-sm font-bold text-text">{label}</span>
          <span className="text-label-sm text-muted">{t("scoreOf")}</span>
        </span>
      )}
      <span className="sr-only">{t("scoreAria")}</span>
    </div>
  );
}

export { C as RING_CIRCUMFERENCE };
