"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useLocale, useTranslations } from "next-intl";
import { AnimatePresence, motion } from "motion/react";
import {
  Check,
  Image as ImageIcon,
  LayoutGrid,
  LoaderCircle,
  LogIn,
  Mic,
  Palette,
  RotateCcw,
  Sparkles,
  Type as TypeIcon,
  Undo2,
  Video as VideoIcon,
  WandSparkles,
} from "lucide-react";
import { Link } from "@/i18n/navigation";
import { Button, buttonVariants } from "@/components/ui/button";
import { Callout } from "@/components/ui/callout";
import {
  ClarifyFields,
  type Pick as ClarifyPick,
} from "@/components/generator/clarify-fields";
import { AI_META, type AiTool, type Kind, type Locale } from "@/lib/ai-tools";
import { type Ratio, RATIOS, RATIO_KINDS, RATIO_SHAPE } from "@/lib/segments";
import type { ClarifyQuestion } from "@/lib/api";
import { ApiError, enrichIdea } from "@/lib/api";
import { fadeUp, stagger } from "@/lib/motion";
import { cn } from "@/lib/utils";

export const MAX_CHARS = 2000;

const TYPES: { value: Kind | null; key: string; Icon: typeof Sparkles }[] = [
  { value: null, key: "kindAuto", Icon: Sparkles },
  { value: "image", key: "kinds.image", Icon: ImageIcon },
  { value: "video", key: "kinds.video", Icon: VideoIcon },
  { value: "app", key: "kinds.app", Icon: LayoutGrid },
  { value: "design", key: "kinds.design", Icon: Palette },
  { value: "text", key: "kinds.text", Icon: TypeIcon },
];

/** Tanlangan / tanlanmagan boshqaruv uslubi (dizayndagi `.opt`). */
const optBase =
  "flex items-center gap-2 rounded-[var(--radius-md)] border text-body-sm font-semibold transition-[background-color,border-color,color] duration-150 disabled:pointer-events-none disabled:opacity-50";
const optOff =
  "border-border-strong bg-surface-2 text-muted hover:border-[color-mix(in_oklab,var(--border-strong),var(--text)_30%)] hover:text-text";
const optOn = "border-selected-border bg-[var(--selected-bg)] text-text";

type Props = {
  text: string;
  onTextChange: (v: string) => void;
  onTextBlur: () => void;
  onSubmit: () => void;

  kind: Kind | null;
  onKind: (k: Kind | null) => void;
  /** Tahlil taxmin qilgan tur (Avto tanlangan boʻlsa koʻrsatiladi) */
  suggestedKind: Kind | null;

  tools: AiTool[];
  ai: AiTool | null;
  onAi: (ai: AiTool | null) => void;
  analyzing: boolean;

  ratio: Ratio;
  onRatio: (r: Ratio) => void;

  questions: ClarifyQuestion[];
  picks: Record<string, ClarifyPick>;
  onPicks: (p: Record<string, ClarifyPick>) => void;

  busy: boolean;
  /** Natija bor — tugma «qayta yaratish» boʻladi */
  hasResult: boolean;
  exhausted: boolean;
  isUser: boolean;
  remainingLabel: string | null;
  onStop: () => void;
  onReset: () => void;
};

type SpeechRec = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start: () => void;
  stop: () => void;
  onresult: ((e: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
};

type SpeechCtor = new () => SpeechRec;

const SPEECH_LANG: Record<Locale, string> = {
  uz: "uz-UZ",
  ru: "ru-RU",
  en: "en-US",
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
  questions,
  picks,
  onPicks,
  busy,
  hasResult,
  exhausted,
  isUser,
  remainingLabel,
  onStop,
  onReset,
}: Props) {
  const t = useTranslations("app");
  const tt = useTranslations("tools");
  const locale = useLocale() as Locale;

  const effectiveKind = kind ?? suggestedKind;
  const showRatio = effectiveKind !== null && RATIO_KINDS.includes(effectiveKind);

  // Ovoz bilan aytish — brauzer Web Speech API'si bor boʻlsa koʻrinadi
  // Workbench faqat brauzerda chiziladi (ssr:false) — qoʻllab-quvvatlash bir marta tekshiriladi
  const [speechReady] = useState(() => {
    if (typeof window === "undefined") return false;
    const w = window as unknown as {
      SpeechRecognition?: SpeechCtor;
      webkitSpeechRecognition?: SpeechCtor;
    };
    return Boolean(w.SpeechRecognition ?? w.webkitSpeechRecognition);
  });
  const [listening, setListening] = useState(false);
  const [voiceError, setVoiceError] = useState(false);
  const recRef = useRef<SpeechRec | null>(null);
  useEffect(() => () => recRef.current?.stop(), []);

  const toggleVoice = useCallback(() => {
    if (listening) {
      recRef.current?.stop();
      return;
    }
    const w = window as unknown as {
      SpeechRecognition?: SpeechCtor;
      webkitSpeechRecognition?: SpeechCtor;
    };
    const Ctor = w.SpeechRecognition ?? w.webkitSpeechRecognition;
    if (!Ctor) return;
    setVoiceError(false);
    const rec = new Ctor();
    recRef.current = rec;
    rec.lang = SPEECH_LANG[locale];
    rec.continuous = false;
    rec.interimResults = false;
    let heard = "";
    rec.onresult = (e) => {
      for (let i = 0; i < e.results.length; i++) {
        heard += e.results[i][0]?.transcript ?? "";
      }
    };
    rec.onerror = () => {
      setVoiceError(true);
      setListening(false);
    };
    rec.onend = () => {
      setListening(false);
      const said = heard.trim();
      if (said) onTextChange(text ? `${text.trimEnd()} ${said}` : said);
    };
    try {
      rec.start();
      setListening(true);
    } catch {
      setVoiceError(true);
    }
  }, [listening, locale, onTextChange, text]);

  // Gʻoyani boyitish — qisqa matnni 2–4 jumlaga kengaytiradi, bir marta qaytarish mumkin
  const [enriching, setEnriching] = useState(false);
  const [enrichError, setEnrichError] = useState<string | null>(null);
  const [beforeEnrich, setBeforeEnrich] = useState<string | null>(null);
  const enrich = async () => {
    const src = text.trim();
    if (src.length < 3 || enriching) return;
    setEnriching(true);
    setEnrichError(null);
    try {
      const better = await enrichIdea(src, locale);
      if (better.trim()) {
        setBeforeEnrich(text);
        onTextChange(better.trim());
      }
    } catch (e) {
      setEnrichError(e instanceof ApiError ? e.message : t("enrichError"));
    } finally {
      setEnriching(false);
    }
  };

  const primaryLabel = busy
    ? t("generating")
    : questions.length
      ? t("continueAnswers")
      : hasResult
        ? t("regenerate")
        : t("generate");

  return (
    <motion.section
      aria-labelledby="h-input"
      className="flex min-w-0 flex-col gap-7 rounded-[var(--radius-xl)] border border-border bg-surface p-5 md:p-7"
      variants={stagger}
      initial="hidden"
      animate="show"
    >
      <motion.div variants={fadeUp} className="flex flex-col gap-2">
        <h1
          id="h-input"
          className="text-[28px] font-extrabold leading-[1.15] tracking-[-0.025em] text-text"
        >
          {t("title")}
        </h1>
        <p className="text-body-md text-muted">{t("subtitle")}</p>
      </motion.div>

      {/* Gʻoya maydoni */}
      <motion.div variants={fadeUp} className="flex flex-col gap-2">
        <div className="flex items-baseline justify-between gap-3">
          <label htmlFor="idea" className="text-body-sm font-bold text-text-2">
            {t("ideaLabel")}
          </label>
          <span className="font-mono text-label-sm text-subtle">
            {t("counter", { n: text.length, max: MAX_CHARS })}
          </span>
        </div>
        <div className="flex flex-col rounded-[var(--radius-lg)] border border-border-strong bg-sunk focus-within:border-accent">
          <textarea
            id="idea"
            rows={4}
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
            className="min-h-28 w-full resize-none rounded-[var(--radius-lg)] bg-transparent px-4 pb-2 pt-4 text-body-md text-text outline-offset-[-2px] placeholder:text-subtle disabled:opacity-60"
          />
          <div className="flex flex-wrap items-center justify-between gap-1 p-2 pl-2.5">
            {speechReady ? (
              <Button
                variant="ghost"
                size="sm"
                className="h-9 gap-2 text-label-md font-semibold"
                aria-pressed={listening}
                disabled={busy}
                onClick={toggleVoice}
              >
                <Mic size={16} className={listening ? "text-error" : undefined} />
                {listening ? t("voiceListening") : t("voice")}
              </Button>
            ) : (
              <span />
            )}
            <div className="flex items-center gap-1">
              {beforeEnrich !== null && !enriching && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-9 gap-2 text-label-md font-semibold"
                  onClick={() => {
                    onTextChange(beforeEnrich);
                    setBeforeEnrich(null);
                  }}
                >
                  <Undo2 size={15} />
                  {t("enrichUndo")}
                </Button>
              )}
              <Button
                variant="ghost"
                size="sm"
                className="h-9 gap-2 text-label-md font-semibold"
                disabled={busy || enriching || text.trim().length < 3}
                onClick={() => void enrich()}
              >
                {enriching ? (
                  <LoaderCircle size={16} className="animate-spin" />
                ) : (
                  <WandSparkles size={16} />
                )}
                {enriching ? t("enriching") : t("enrich")}
              </Button>
            </div>
          </div>
        </div>
        {(voiceError || enrichError) && (
          <p className="text-body-sm text-error">
            {voiceError ? t("voiceError") : enrichError}
          </p>
        )}
      </motion.div>

      {/* Aniqlashtiruvchi savollar — ixtiyoriy */}
      <AnimatePresence initial={false}>
        {questions.length > 0 && (
          <motion.div
            key="clarify"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 4, transition: { duration: 0.15 } }}
          >
            <ClarifyFields
              questions={questions}
              picks={picks}
              onChange={onPicks}
              onSubmit={onSubmit}
              disabled={busy}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Natija turi */}
      <motion.fieldset variants={fadeUp} className="m-0 border-0 p-0">
        <legend className="mb-2.5 p-0 text-body-sm font-bold text-text-2">
          {t("typeLabel")}
        </legend>
        <div className="grid grid-cols-3 gap-2">
          {TYPES.map(({ value, key, Icon }) => {
            const on = kind === value;
            // «Avto» tanlangan boʻlsa tahlil taxmin qilgan tur nuqta bilan belgilanadi
            const guessed = kind === null && value !== null && value === suggestedKind;
            return (
              <button
                key={key}
                type="button"
                aria-pressed={on}
                disabled={busy}
                onClick={() => onKind(value)}
                title={guessed ? t("kindSuggested", { kind: t(`kinds.${value}`) }) : undefined}
                className={cn(optBase, on ? optOn : optOff, "h-11 justify-start px-3")}
              >
                <Icon size={16} className="shrink-0" />
                <span className="truncate">{t(key)}</span>
                {guessed && (
                  <span
                    aria-hidden
                    className="ml-auto h-1.5 w-1.5 shrink-0 rounded-full bg-accent"
                  />
                )}
              </button>
            );
          })}
        </div>
      </motion.fieldset>

      {/* Model */}
      <motion.fieldset variants={fadeUp} className="m-0 border-0 p-0">
        <legend className="mb-2.5 flex items-center gap-2 p-0 text-body-sm font-bold text-text-2">
          {t("modelLabel")}
          {analyzing && (
            <span className="inline-flex items-center gap-1.5 font-normal text-label-sm text-subtle">
              <LoaderCircle size={12} className="animate-spin" />
              {tt("analyzing")}
            </span>
          )}
        </legend>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {tools.length === 0 && (
            <ModelCard
              on={ai === null}
              name={t("modelAuto")}
              version=""
              sub={t("modelAutoSub")}
              dot="var(--muted)"
              disabled={busy}
              onClick={() => onAi(null)}
            />
          )}
          {tools.map((tool) => (
            <ModelCard
              key={tool}
              on={ai === tool}
              name={AI_META[tool].name}
              version={AI_META[tool].version}
              sub={tt(`sub.${tool}`)}
              dot={AI_META[tool].dot}
              disabled={busy}
              onClick={() => onAi(tool)}
            />
          ))}
        </div>
      </motion.fieldset>

      {/* Nisbat — faqat rasm/video */}
      <AnimatePresence initial={false}>
        {showRatio && (
          <motion.fieldset
            key="ratio"
            className="m-0 border-0 p-0"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 4, transition: { duration: 0.15 } }}
          >
            <legend className="mb-2.5 p-0 text-body-sm font-bold text-text-2">
              {t("ratioLabel")}
            </legend>
            <div className="flex flex-wrap gap-2">
              {RATIOS.map((r) => {
                const on = ratio === r;
                const { w, h } = RATIO_SHAPE[r];
                return (
                  <button
                    key={r}
                    type="button"
                    aria-pressed={on}
                    disabled={busy}
                    onClick={() => onRatio(r)}
                    className={cn(
                      optBase,
                      on ? optOn : optOff,
                      "h-11 min-w-16 justify-center px-3.5 font-mono text-code-sm font-medium",
                    )}
                  >
                    <span
                      aria-hidden
                      className="inline-block rounded-[2px] border-[1.5px] border-current"
                      style={{ width: w, height: h }}
                    />
                    {r}
                  </button>
                );
              })}
            </div>
          </motion.fieldset>
        )}
      </AnimatePresence>

      {/* Asosiy harakat */}
      <motion.div variants={fadeUp} className="flex flex-col gap-3">
        {busy ? (
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
          <div className="flex min-h-10 flex-col items-center gap-1">
            {(text || hasResult) && (
              <Button variant="ghost" size="sm" className="h-10 gap-2" onClick={onReset}>
                <RotateCcw size={15} />
                {t("reset")}
              </Button>
            )}
            <p className="font-mono text-label-sm text-subtle">{remainingLabel}</p>
          </div>
        )}
      </motion.div>
    </motion.section>
  );
}

function ModelCard({
  on,
  name,
  version,
  sub,
  dot,
  disabled,
  onClick,
}: {
  on: boolean;
  name: string;
  version: string;
  sub: string;
  dot: string;
  disabled?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      aria-pressed={on}
      disabled={disabled}
      onClick={onClick}
      className={cn(
        optBase,
        on ? optOn : optOff,
        "min-h-16 items-start justify-between gap-2 rounded-[var(--radius-lg)] px-3.5 py-3 text-left",
      )}
    >
      <span className="flex min-w-0 flex-col gap-1">
        <span className="flex min-w-0 items-center gap-2 text-body-md font-bold text-text">
          <span
            aria-hidden
            className="h-2 w-2 shrink-0 rounded-full"
            style={{ background: dot }}
          />
          <span className="truncate">{name}</span>
          {version && (
            <span className="shrink-0 font-mono text-label-sm font-medium text-subtle">
              {version}
            </span>
          )}
        </span>
        <span className="text-body-sm font-medium text-muted">{sub}</span>
      </span>
      {on && (
        <span
          aria-hidden
          className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-accent text-on-accent"
        >
          <Check size={12} strokeWidth={3} />
        </span>
      )}
    </button>
  );
}
