"use client";

import { useCallback, useEffect, useId, useLayoutEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { Check, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

export type PickerOption<T extends string> = {
  value: T;
  label: string;
  /** Qisqa izoh (versiya yoki tavsif) */
  hint?: string;
  /** 8px nuqta (AI brendi) */
  dot?: string;
  icon?: React.ReactNode;
};

type Props<T extends string> = {
  /** Ekran oʻquvchisi uchun nom («Natija turi») */
  label: string;
  value: T;
  options: PickerOption<T>[];
  onChange: (v: T) => void;
  disabled?: boolean;
  /** Qiymat sayt tomonidan aniqlangan (foydalanuvchi oʻzi tanlamagan) */
  auto?: boolean;
  className?: string;
};

type Pos = { left: number; width: number; top?: number; bottom?: number };

const LIST_MIN_W = 230;
const GAP = 6;

/**
 * Ixcham tanlov: bitta qatorda joriy qiymat, bosilganda roʻyxat ochiladi.
 * Roʻyxat `position: fixed` — panelning ichki skrolli uni kesmaydi.
 */
export function Picker<T extends string>({
  label,
  value,
  options,
  onChange,
  disabled,
  auto,
  className,
}: Props<T>) {
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState<Pos | null>(null);
  const btnRef = useRef<HTMLButtonElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const id = useId();
  const current = options.find((o) => o.value === value) ?? options[0];

  const place = useCallback(() => {
    const el = btnRef.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const width = Math.max(r.width, LIST_MIN_W);
    const left = Math.min(Math.max(8, r.left), window.innerWidth - width - 8);
    // Pastda joy boʻlmasa — yuqoriga ochiladi
    const need = Math.min(options.length * 48 + 12, 288);
    const below = window.innerHeight - r.bottom - GAP;
    setPos(
      below >= need || below >= r.top
        ? { left, width, top: r.bottom + GAP }
        : { left, width, bottom: window.innerHeight - r.top + GAP },
    );
  }, [options.length]);

  useLayoutEffect(() => {
    if (open) place();
  }, [open, place]);

  useEffect(() => {
    if (!open) return;
    const close = () => setOpen(false);
    const onDown = (e: MouseEvent) => {
      const t = e.target as Node;
      if (!btnRef.current?.contains(t) && !listRef.current?.contains(t)) close();
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        close();
        btnRef.current?.focus();
      }
    };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    // Skroll yoki oʻlcham oʻzgarsa roʻyxat joyidan qoladi — yopiladi
    window.addEventListener("resize", close);
    window.addEventListener("scroll", close, true);
    listRef.current?.querySelector<HTMLButtonElement>("[data-opt]")?.focus();
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
      window.removeEventListener("resize", close);
      window.removeEventListener("scroll", close, true);
    };
  }, [open]);

  const move = (from: number, step: number) => {
    const next = (from + step + options.length) % options.length;
    listRef.current?.querySelectorAll<HTMLButtonElement>("[data-opt]")[next]?.focus();
  };

  if (!current) return null;

  return (
    <div className={cn("min-w-0", className)}>
      <button
        ref={btnRef}
        type="button"
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={open ? id : undefined}
        aria-label={`${label}: ${current.label}`}
        onClick={() => setOpen((v) => !v)}
        className={cn(
          "flex h-10 w-full min-w-0 items-center gap-2 rounded-[var(--radius-md)] border px-3",
          "text-body-sm font-semibold transition-[background-color,border-color,color] duration-150",
          "disabled:pointer-events-none disabled:opacity-50",
          open
            ? "border-selected-border bg-[var(--selected-bg)] text-text"
            : "border-border-strong bg-surface-2 text-text hover:border-[color-mix(in_oklab,var(--border-strong),var(--text)_30%)]",
        )}
      >
        {current.dot && (
          <span
            aria-hidden
            className="h-2 w-2 shrink-0 rounded-full"
            style={{ background: current.dot }}
          />
        )}
        {current.icon}
        <span className="truncate">{current.label}</span>
        {auto && (
          <span
            aria-hidden
            title={label}
            className="shrink-0 text-label-sm font-bold text-accent"
          >
            ✦
          </span>
        )}
        <ChevronDown size={15} className="ml-auto shrink-0 text-subtle" />
      </button>

      <AnimatePresence>
        {open && pos && (
          <motion.div
            ref={listRef}
            role="listbox"
            aria-label={label}
            id={id}
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4, transition: { duration: 0.12 } }}
            transition={{ duration: 0.15, ease: [0.16, 1, 0.3, 1] }}
            style={{
              position: "fixed",
              left: pos.left,
              width: pos.width,
              ...(pos.top !== undefined ? { top: pos.top } : { bottom: pos.bottom }),
            }}
            className="z-50 flex max-h-72 flex-col gap-0.5 overflow-y-auto rounded-[var(--radius-lg)] border border-border-strong bg-surface p-1.5 shadow-[0_18px_40px_-12px_var(--scrim)]"
          >
            {options.map((o, i) => {
              const on = o.value === value;
              return (
                <button
                  key={o.value}
                  data-opt
                  type="button"
                  role="option"
                  aria-selected={on}
                  onKeyDown={(e) => {
                    if (e.key === "ArrowDown") {
                      e.preventDefault();
                      move(i, 1);
                    } else if (e.key === "ArrowUp") {
                      e.preventDefault();
                      move(i, -1);
                    }
                  }}
                  onClick={() => {
                    onChange(o.value);
                    setOpen(false);
                    btnRef.current?.focus();
                  }}
                  className={cn(
                    "flex min-h-11 items-center gap-2.5 rounded-[var(--radius-md)] px-2.5 py-2 text-left",
                    "text-body-sm font-semibold transition-colors",
                    on ? "bg-[var(--selected-bg)] text-text" : "text-text-2 hover:bg-surface-2",
                  )}
                >
                  {o.dot && (
                    <span
                      aria-hidden
                      className="h-2 w-2 shrink-0 rounded-full"
                      style={{ background: o.dot }}
                    />
                  )}
                  {o.icon}
                  <span className="flex min-w-0 flex-col">
                    <span className="truncate">{o.label}</span>
                    {o.hint && (
                      <span className="truncate text-label-sm font-medium text-muted">
                        {o.hint}
                      </span>
                    )}
                  </span>
                  {on && <Check size={15} className="ml-auto shrink-0 text-accent" />}
                </button>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
