"use client";

import { useTranslations } from "next-intl";
import {
  Image as ImageIcon,
  LayoutGrid,
  LoaderCircle,
  LogIn,
  Palette,
  RotateCcw,
  Sparkles,
  Type as TypeIcon,
  Video as VideoIcon,
} from "lucide-react";
import { Link } from "@/i18n/navigation";
import { Button, buttonVariants } from "@/components/ui/button";
import { Callout } from "@/components/ui/callout";
import { Picker, type PickerOption } from "@/components/generator/picker";
import { AI_META, type AiTool, type Kind } from "@/lib/ai-tools";
import { type Ratio, RATIOS, RATIO_KINDS, RATIO_SHAPE } from "@/lib/segments";
import { cn } from "@/lib/utils";

export const MAX_CHARS = 2000;

const KIND_ICON: Record<Kind, React.ReactNode> = {
  image: <ImageIcon size={15} className="shrink-0" />,
  video: <VideoIcon size={15} className="shrink-0" />,
  app: <LayoutGrid size={15} className="shrink-0" />,
  design: <Palette size={15} className="shrink-0" />,
  text: <TypeIcon size={15} className="shrink-0" />,
};
const KINDS: Kind[] = ["image", "video", "app", "design", "text"];

type Props = {
  text: string;
  onTextChange: (v: string) => void;
  onTextBlur: () => void;
  onSubmit: () => void;

  kind: Kind | null;
  onKind: (k: Kind | null) => void;
  /** Tahlil taxmin qilgan tur */
  suggestedKind: Kind | null;

  tools: AiTool[];
  ai: AiTool | null;
  onAi: (ai: AiTool | null) => void;
  analyzing: boolean;

  ratio: Ratio;
  onRatio: (r: Ratio) => void;

  /** Savollar oʻng panelda — chapdagi asosiy tugma yashiriladi */
  clarifying: boolean;
  /** Tur/model/nisbat faqat natija boʻlgach koʻrsatiladi */
  showDecisions: boolean;

  busy: boolean;
  hasResult: boolean;
  exhausted: boolean;
  isUser: boolean;
  onStop: () => void;
  onReset: () => void;
};

export function IdeaPanel({
  text,
  onTextChange,
  onTextBlur,
  onSubmit,
  kind,
  onKind,
  suggestedKind,
  tools,
  ai,
  onAi,
  analyzing,
  ratio,
  onRatio,
  clarifying,
  showDecisions,
  busy,
  hasResult,
  exhausted,
  isUser,
  onStop,
  onReset,
}: Props) {
  const t = useTranslations("app");
  const tt = useTranslations("tools");

  const effectiveKind = kind ?? suggestedKind;
  const showRatio = effectiveKind !== null && RATIO_KINDS.includes(effectiveKind);

  // Qaror qatori: tur / model / nisbat. Qiymatlar gʻoyadan aniqlanadi,
  // bosilganda roʻyxat ochiladi — shuning uchun bitta qator joy egallaydi.
  const kindOptions: PickerOption<string>[] = [
    {
      value: "auto",
      label: t("kindAuto"),
      icon: <Sparkles size={15} className="shrink-0" />,
    },
    ...KINDS.map((k) => ({ value: k, label: t(`kinds.${k}`), icon: KIND_ICON[k] })),
  ];
  // «Avto» tanlangan boʻlsa tahlil aniqlagan tur koʻrsatiladi
  const kindValue: string = kind ?? suggestedKind ?? "auto";

  const modelOptions: PickerOption<string>[] = tools.length
    ? tools.map((tool) => ({
        value: tool,
        label: AI_META[tool].name,
        hint: AI_META[tool].version || tt(`sub.${tool}`),
        dot: AI_META[tool].dot,
      }))
    : [{ value: "auto", label: t("modelAuto"), hint: t("modelAutoSub") }];
  const modelValue: string = ai ?? "auto";

  const ratioOptions: PickerOption<Ratio>[] = RATIOS.map((r) => ({
    value: r,
    label: r,
    icon: (
      <span
        aria-hidden
        className="inline-block shrink-0 rounded-[2px] border-[1.5px] border-current"
        style={{ width: RATIO_SHAPE[r].w, height: RATIO_SHAPE[r].h }}
      />
    ),
  }));

  const primaryLabel = busy
    ? t("generating")
    : hasResult
      ? t("regenerate")
      : t("generate");

  return (
    <section
      aria-labelledby="h-input"
      className="flex min-h-0 min-w-0 flex-col gap-4 rounded-[var(--radius-xl)] border border-border bg-surface p-5 md:p-6 lg:h-full lg:overflow-y-auto"
    >
      <div className="flex shrink-0 flex-col gap-1.5">
        <h1
          id="h-input"
          className="text-[26px] font-extrabold leading-[1.15] tracking-[-0.025em] text-text"
        >
          {t("title")}
        </h1>
        <p className="text-body-sm text-muted">{t("subtitle")}</p>
      </div>

      {/* Gʻoya maydoni — qolgan boʻsh joyni oʻzi egallaydi */}
      <div className="flex min-h-0 flex-1 flex-col gap-2">
        <div className="flex items-baseline justify-between gap-3">
          <label htmlFor="idea" className="text-body-sm font-bold text-text-2">
            {t("ideaLabel")}
          </label>
          <span className="font-mono text-label-sm text-subtle">
            {t("counter", { n: text.length, max: MAX_CHARS })}
          </span>
        </div>
        <div className="flex min-h-0 flex-1 flex-col rounded-[var(--radius-lg)] border border-border-strong bg-sunk focus-within:border-accent">
          <textarea
            id="idea"
            rows={3}
            maxLength={MAX_CHARS}
            value={text}
            disabled={busy}
            placeholder={t("placeholder")}
            onChange={(e) => onTextChange(e.target.value)}
            onBlur={onTextBlur}
            onKeyDown={(e) => {
              if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
                e.preventDefault();
                onSubmit();
              }
            }}
            className="min-h-24 w-full flex-1 resize-none rounded-[var(--radius-lg)] bg-transparent px-4 pb-2 pt-3.5 text-body-md text-text outline-offset-[-2px] placeholder:text-subtle disabled:opacity-60"
          />
        </div>
      </div>

      {/* Qaror qatori — prompt yasalgandan keyin: nima tanlangani koʻrinadi va oʻzgartiriladi */}
      {showDecisions && (
      <div className="flex shrink-0 flex-col gap-2">
        <div className="flex flex-wrap items-baseline gap-x-2">
          <span className="text-body-sm font-bold text-text-2">{t("decisions")}</span>
          <span className="inline-flex min-h-5 items-center gap-1.5 text-label-sm text-subtle">
            {analyzing ? (
              <>
                <LoaderCircle size={12} className="animate-spin" />
                {tt("analyzing")}
              </>
            ) : (
              t("decisionsHint")
            )}
          </span>
        </div>
        <div className="flex min-w-0 gap-2">
          <Picker
            label={t("typeLabel")}
            value={kindValue}
            options={kindOptions}
            disabled={busy}
            onChange={(v) => onKind(v === "auto" ? null : (v as Kind))}
            className="flex-[3]"
          />
          <Picker
            label={t("modelLabel")}
            value={modelValue}
            options={modelOptions}
            disabled={busy || !tools.length}
            onChange={(v) => onAi(v === "auto" ? null : (v as AiTool))}
            className="flex-[4]"
          />
          {showRatio && (
            <Picker
              label={t("ratioLabel")}
              value={ratio}
              options={ratioOptions}
              disabled={busy}
              onChange={onRatio}
              className="w-[104px] shrink-0"
            />
          )}
        </div>
      </div>
      )}

      {/* Asosiy harakat */}
      <div className="flex shrink-0 flex-col gap-2">
        {clarifying && !busy ? null : busy ? (
          <Button
            variant="secondary"
            className="h-13 w-full justify-center gap-2.5 rounded-[var(--radius-lg)] text-body-md font-bold"
            onClick={onStop}
          >
            <LoaderCircle size={18} className="animate-spin" />
            {primaryLabel}
            <span className="ml-1 font-normal text-body-sm text-muted">{t("stop")}</span>
          </Button>
        ) : (
          <Button
            variant="primary"
            className="h-13 w-full justify-center gap-2.5 rounded-[var(--radius-lg)] text-body-md font-bold"
            disabled={exhausted || text.trim().length < 3}
            onClick={onSubmit}
          >
            <Sparkles size={18} />
            {primaryLabel}
          </Button>
        )}

        {exhausted ? (
          <Callout
            tone="error"
            className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"
          >
            <span>{isUser ? t("userExhausted") : t("guestExhausted")}</span>
            {!isUser && (
              <Link
                href="/login"
                className={cn(
                  buttonVariants({ variant: "secondary", size: "sm" }),
                  "shrink-0",
                )}
              >
                <LogIn size={16} />
                {t("loginGoogle")}
              </Link>
            )}
          </Callout>
        ) : (
          <div className="flex min-h-9 items-center justify-center">
            {(text || hasResult) && (
              <Button variant="ghost" size="sm" className="h-9 gap-2" onClick={onReset}>
                <RotateCcw size={14} />
                {t("reset")}
              </Button>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
