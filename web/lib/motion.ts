// Umumiy animatsiya tokenlari va variantlar (motion/react). Faqat transform/opacity.
import type { Variants } from "motion/react";

export const EASE_OUT = [0.16, 1, 0.3, 1] as const;
export const DUR = { fast: 0.15, base: 0.2, slow: 0.3 } as const;

/** Bolalarni 50 ms oraliq bilan chiqaradi */
export const stagger: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.05, delayChildren: 0.05 } },
};

export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 8 },
  show: { opacity: 1, y: 0, transition: { duration: DUR.slow, ease: EASE_OUT } },
};

export const fade: Variants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { duration: DUR.base } },
};

/** Kichik element almashinuvi (AnimatePresence mode="wait") */
export const swap = {
  initial: { opacity: 0, y: 4 },
  animate: { opacity: 1, y: 0, transition: { duration: DUR.base, ease: EASE_OUT } },
  exit: { opacity: 0, y: -4, transition: { duration: DUR.fast } },
} as const;

export const springPop = { type: "spring", stiffness: 420, damping: 22, mass: 0.6 } as const;
