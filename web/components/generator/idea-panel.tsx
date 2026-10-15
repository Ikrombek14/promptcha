"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useLocale, useTranslations } from "next-intl";
import {
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
import { Picker, type PickerOption } from "@/components/generator/picker";
import { AI_META, type AiTool, type Kind, type Locale } from "@/lib/ai-tools";
import { type Ratio, RATIOS, RATIO_KINDS, RATIO_SHAPE } from "@/lib/segments";
import { ApiError, enrichIdea } from "@/lib/api";
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
  /** Vositani foydalanuvchi oʻzi tanlagan (aks holda tahlil tanlagan) */
  aiPicked: boolean;
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
  onresult:
    | ((e: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void)
    | null;
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
  aiPicked,
  analyzing,
  ratio,
  onRatio,
  clarifying,
  showDecisions,
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
  // «Avto» tanlangan boʻlsa tahlil aniqlagan tur koʻrsatiladi (✦ belgisi bilan)
  const kindValue: string = kind ?? suggestedKind ?? "auto";
  const kindIsAuto = kind === null && suggestedKind !== null;

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
          <div className="flex flex-wrap items-center justify-between gap-1 p-1.5 pl-2">
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
            auto={kindIsAuto}
            disabled={busy}
            onChange={(v) => onKind(v === "auto" ? null : (v as Kind))}
            className="flex-[3]"
          />
          <Picker
            label={t("modelLabel")}
            value={modelValue}
            options={modelOptions}
            auto={!aiPicked && tools.length > 0}
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
          <div className="flex min-h-9 items-center justify-center gap-3">
            {(text || hasResult) && (
              <Button variant="ghost" size="sm" className="h-9 gap-2" onClick={onReset}>
                <RotateCcw size={14} />
                {t("reset")}
              </Button>
            )}
            <p className="font-mono text-label-sm text-subtle">{remainingLabel}</p>
          </div>
        )}
      </div>
    </section>
  );
}
