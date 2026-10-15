"use client";

// Tarix/Kutubxona kartasi: sana + chiplar + sifat halqasi, gʻoya, prompt boshlanishi, amallar.
// Uslub: promptcha-redesign/design/reference/Main.dc.html (chip 9999px, halqa #5FD3B5, sunk blok).

import { useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { Bookmark, Check, Copy, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AI_META, KINDS, type AiTool, type Kind } from "@/lib/ai-tools";
import type { SavedPrompt } from "@/lib/pages-api";
import { useDateTime } from "@/components/pages/use-list";
import { cn } from "@/lib/utils";

function Chip({ dot, children }: { dot?: string; children: React.ReactNode }) {
  return (
    <span className="inline-flex h-7 items-center gap-1.5 rounded-full border border-border bg-surface-2 px-2.5 text-label-sm font-bold text-muted">
      {dot && (
        <span
          aria-hidden
          className="h-2 w-2 shrink-0 rounded-full"
          style={{ background: dot }}
        />
      )}
      {children}
    </span>
  );
}

/** 36px aylana progress — ball ichida (tugma emas) */
function ScoreRing({ value, label }: { value: number; label: string }) {
  const r = 15;
  const c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, Math.round(value)));
  return (
    <span
      role="img"
      aria-label={label}
      title={label}
      className="relative inline-flex h-9 w-9 shrink-0 items-center justify-center"
    >
      <svg
        viewBox="0 0 36 36"
        className="absolute inset-0 -rotate-90"
        aria-hidden
      >
        <circle
          cx="18"
          cy="18"
          r={r}
          fill="none"
          stroke="var(--border-strong)"
          strokeWidth="3"
        />
        <circle
          cx="18"
          cy="18"
          r={r}
          fill="none"
          stroke="var(--quality)"
          strokeWidth="3"
          strokeLinecap="round"
          strokeDasharray={`${(c * pct) / 100} ${c}`}
        />
      </svg>
      <span className="text-label-sm font-extrabold tabular-nums text-text">
        {pct}
      </span>
    </span>
  );
}

type Props = {
  item: SavedPrompt;
  mode: "history" | "library";
  onToggleSave: (item: SavedPrompt) => Promise<void>;
  onDelete: (item: SavedPrompt) => Promise<void>;
};

export function PromptCard({ item, mode, onToggleSave, onDelete }: Props) {
  const t = useTranslations("pages.common");
  const tk = useTranslations("pages.kinds");
  const dateTime = useDateTime();

  const [copied, setCopied] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState<"save" | "delete" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(
    () => () => {
      if (timer.current) clearTimeout(timer.current);
    },
    [],
  );

  const kindKey = (KINDS as readonly string[]).includes(item.kind ?? "")
    ? (item.kind as Kind)
    : null;
  const meta = item.ai ? AI_META[item.ai as AiTool] : undefined;

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(item.result);
      setCopied(true);
      if (timer.current) clearTimeout(timer.current);
      timer.current = setTimeout(() => setCopied(false), 1800);
    } catch {
      setError(t("copyFailed"));
    }
  };

  const run = async (kind: "save" | "delete") => {
    if (busy) return;
    setBusy(kind);
    setError(null);
    try {
      if (kind === "save") await onToggleSave(item);
      else await onDelete(item);
      setConfirming(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  };

  return (
    <li className="flex flex-col gap-3 rounded-[var(--radius-xl)] border border-border bg-surface p-4 md:p-5">
      <div className="flex flex-wrap items-center gap-2">
        <time
          dateTime={item.created_at}
          className="font-mono text-code-sm text-subtle"
        >
          {dateTime(item.created_at)}
        </time>
        {kindKey && <Chip>{tk(kindKey)}</Chip>}
        {item.ai && <Chip dot={meta?.dot}>{meta?.name ?? item.ai}</Chip>}
        <span className="flex-1" />
        {item.score !== null && item.score !== undefined && (
          <ScoreRing
            value={item.score}
            label={t("scoreLabel", { score: Math.round(item.score) })}
          />
        )}
      </div>

      <div className="flex min-w-0 flex-col gap-2">
        <p className="truncate text-body-md font-semibold text-text">
          <span className="sr-only">{t("idea")}: </span>
          {item.input_text}
        </p>
        <p className="line-clamp-2 rounded-[var(--radius-md)] border border-border bg-sunk px-3 py-2 font-mono text-code-sm text-muted">
          <span className="sr-only">{t("prompt")}: </span>
          {item.result}
        </p>
      </div>

      <div
        className="flex flex-wrap items-center gap-2"
        onKeyDown={(e) => {
          if (e.key === "Escape" && confirming) setConfirming(false);
        }}
      >
        {confirming ? (
          <>
            <span className="text-body-sm font-semibold text-text">
              {t("deleteAsk")}
            </span>
            <Button
              autoFocus
              variant="secondary"
              className="min-h-11 border-error text-error"
              disabled={busy !== null}
              onClick={() => void run("delete")}
            >
              <Trash2 size={16} aria-hidden />
              {t("deleteYes")}
            </Button>
            <Button
              variant="ghost"
              className="min-h-11"
              disabled={busy !== null}
              onClick={() => setConfirming(false)}
            >
              {t("deleteNo")}
            </Button>
          </>
        ) : (
          <>
            <Button variant="secondary" className="min-h-11" onClick={copy}>
              {copied ? (
                <Check size={16} aria-hidden className="text-quality" />
              ) : (
                <Copy size={16} aria-hidden />
              )}
              {copied ? t("copied") : t("copy")}
            </Button>
            <Button
              variant="secondary"
              className={cn("min-h-11", item.is_saved && "text-text")}
              aria-pressed={item.is_saved}
              disabled={busy !== null}
              onClick={() => void run("save")}
            >
              <Bookmark
                size={16}
                aria-hidden
                fill={item.is_saved ? "currentColor" : "none"}
              />
              {item.is_saved
                ? mode === "library"
                  ? t("unsave")
                  : t("saved")
                : t("save")}
            </Button>
            <Button
              variant="ghost"
              className="min-h-11"
              disabled={busy !== null}
              onClick={() => setConfirming(true)}
            >
              <Trash2 size={16} aria-hidden />
              {t("delete")}
            </Button>
          </>
        )}
      </div>

      {error && (
        <p role="alert" className="text-body-sm text-error">
          {error}
        </p>
      )}
    </li>
  );
}
