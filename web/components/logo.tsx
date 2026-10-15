"use client";

import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";

/**
 * Promptcha logosi — matnning oʻzi: «Prompt» yorugʻ, «cha» kulrang (Manrope 800).
 * Oʻlchamni `font-size` beradi (header 24px, mobil 22px).
 *
 * Holatlar (`state`):
 *   breathe — sahifa ochilganda shaffoflik toʻlqini harflar boʻylab yuradi (doimiy)
 *   loading — prompt yasalayotganda (tezroq toʻlqin)
 *   done    — natija kelganda bir marta sakrash
 * Animatsiyalar `globals.css` da (`.pw`), `prefers-reduced-motion` hurmat qilinadi.
 */
export type LogoState = "breathe" | "loading" | "done" | null;

const LETTERS = [
  { ch: "P", i: 0, cha: false },
  { ch: "r", i: 1, cha: false },
  { ch: "o", i: 2, cha: false },
  { ch: "m", i: 3, cha: false },
  { ch: "p", i: 4, cha: false },
  { ch: "t", i: 5, cha: false },
  { ch: "c", i: 6, cha: true },
  { ch: "h", i: 7, cha: true },
  { ch: "a", i: 8, cha: true },
];

export function Logo({
  state = "breathe",
  className,
  interactive = true,
}: {
  state?: LogoState;
  className?: string;
  interactive?: boolean;
}) {
  const ref = useRef<HTMLSpanElement>(null);

  // `done` har safar boshidan oʻynashi uchun animatsiyani qayta ishga tushiramiz
  useEffect(() => {
    const el = ref.current;
    if (!el || state !== "done") return;
    el.classList.remove("v-done");
    void el.getBoundingClientRect();
    el.classList.add("v-done");
  }, [state]);

  return (
    <span
      ref={ref}
      role="img"
      aria-label="Promptcha"
      className={cn(
        "pw",
        state === "breathe" && "v-breathe",
        state === "loading" && "v-loading",
        state === "done" && "v-done",
        interactive && "v-interactive",
        className,
      )}
    >
      <span aria-hidden="true">
        {LETTERS.map(({ ch, i, cha }) => (
          <span
            key={i}
            className={cn("l", cha && "c")}
            style={{ "--i": i } as React.CSSProperties}
          >
            {ch}
          </span>
        ))}
      </span>
    </span>
  );
}
