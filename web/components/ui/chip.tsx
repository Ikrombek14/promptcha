"use client";

import * as React from "react";
import { motion, type HTMLMotionProps } from "motion/react";
import { cn } from "@/lib/utils";

type ChipProps = Omit<HTMLMotionProps<"button">, "children"> & {
  selected?: boolean;
  /** "ink" — tanlanganda qora fon (yoʻnalish); "outline" — accent chegara (AI vositasi) */
  tone?: "ink" | "outline";
  dot?: string;
  /**
   * Bir guruh ichida bitta id: tanlangan holat belgisi chipdan chipga sirpanib oʻtadi
   * (LayoutGroup ichida ishlating). Berilmasa — oddiy rang almashinuvi.
   */
  indicatorId?: string;
  children?: React.ReactNode;
};

const INDICATOR_SPRING = { type: "spring", stiffness: 520, damping: 38, mass: 0.7 } as const;

export function Chip({
  selected,
  tone = "ink",
  dot,
  indicatorId,
  className,
  children,
  ...props
}: ChipProps) {
  const sliding = !!indicatorId;
  return (
    <motion.button
      type="button"
      aria-pressed={selected}
      whileTap={{ scale: 0.97 }}
      transition={{ duration: 0.1 }}
      className={cn(
        "relative inline-flex h-9 min-w-0 items-center gap-2 whitespace-nowrap rounded-[var(--radius-sm)] border px-3 text-label-md font-medium transition-colors duration-200 select-none",
        "disabled:pointer-events-none disabled:opacity-50",
        !selected && "border-border bg-surface-2 text-text hover:border-muted",
        selected && sliding && "border-transparent bg-transparent",
        selected && !sliding && tone === "ink" && "border-text bg-text text-bg",
        selected && !sliding && tone === "outline" && "border-accent bg-surface text-text",
        selected && sliding && tone === "ink" && "text-bg",
        selected && sliding && tone === "outline" && "text-text",
        className,
      )}
      {...props}
    >
      {selected && sliding && (
        <motion.span
          layoutId={indicatorId}
          aria-hidden
          transition={INDICATOR_SPRING}
          className={cn(
            "absolute inset-0 rounded-[var(--radius-sm)] border",
            tone === "ink" ? "border-text bg-text" : "border-accent bg-surface",
          )}
        />
      )}
      {dot && (
        <span
          aria-hidden
          className="relative z-10 inline-block h-2 w-2 shrink-0 rounded-full"
          style={{ background: dot }}
        />
      )}
      <span className="relative z-10 inline-flex min-w-0 items-center gap-2">{children}</span>
    </motion.button>
  );
}
