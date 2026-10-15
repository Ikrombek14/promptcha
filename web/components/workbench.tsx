"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  useSyncExternalStore,
} from "react";
import { useLocale, useTranslations } from "next-intl";
import { AnimatePresence, MotionConfig } from "motion/react";
import { Check, Copy, Pencil, RotateCcw, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { IdeaPanel } from "@/components/generator/idea-panel";
import { ResultPanel } from "@/components/generator/result-panel";
import {
  ClarifyCard,
  EmptyResult,
  ErrorResult,
  LoadingResult,
} from "@/components/generator/result-states";
import {
  type Pick as ClarifyPick,
  toAnswers,
} from "@/components/generator/clarify-fields";
import { AI_META, type Kind, type Locale } from "@/lib/ai-tools";
import { type Ratio, RATIO_KINDS } from "@/lib/segments";
import {
  ApiError,
  type ImproveBody,
  analyze,
  cancelJob,
  jobEvents,
  savePrompt,
  startGenerate,
} from "@/lib/api";
import { type Draft, EMPTY_DRAFT, loadDraft, saveDraft } from "@/lib/draft";
import { sessionId, track } from "@/lib/events";
import {
  guestRemaining,
  readGuest,
  saveGuestPrompt,
  subscribeGuest,
  takeGuestPrompts,
} from "@/lib/guest";
import {
  currentUser,
  migrateGuestPrompts,
  refreshUser,
  useUser,
} from "@/lib/auth";

const getServerRemaining = () => null;

export function Workbench() {
  const t = useTranslations("app");
  const tr = useTranslations("result");
  const tc = useTranslations("clarify");
  const ta = useTranslations("auth");
  const locale = useLocale() as Locale;
  const user = useUser();

  // Butun holat bitta obyektda — localStorage'ga yoziladi, yangilanganda tiklanadi
  const [s, setS] = useState<Draft>(loadDraft);
  const patch = useCallback(
    (p: Partial<Draft>) => setS((prev) => ({ ...prev, ...p })),
    [],
  );
  const stateRef = useRef(s);

  useEffect(() => {
    stateRef.current = s;
    saveDraft(s);
  }, [s]);

  const guestLeft = useSyncExternalStore<number | null>(
    subscribeGuest,
    guestRemaining,
    getServerRemaining,
  );
  // Qoldiq: kirgan → serverdagi kunlik limit (Pro'da null → cheksiz);
  // kirmagan → guest hisobi; hali yuklanmagan → koʻrsatilmaydi
  const remaining: number | null = user
    ? user.remaining_today
    : user === null
      ? guestLeft
      : null;
  const remainingLabel: string | null = user
    ? user.remaining_today === null
      ? null
      : ta("remainingToday", { n: user.remaining_today })
    : remaining !== null
      ? t("guestLeft", { n: remaining })
      : null;
  const abortRef = useRef<AbortController | null>(null);

  const busy = s.phase === "loading" || s.phase === "streaming";
  const exhausted = remaining !== null && remaining <= 0;

  // Savol javoblari (chapdagi chiplar) — ish tugagach tozalanadi
  const [picks, setPicks] = useState<Record<string, ClarifyPick>>({});
  // Mobil: natija chiqqach gʻoya paneli yigʻiladi, «Tahrirlash» bilan ochiladi
  const [editing, setEditing] = useState(false);
  const [copiedBar, setCopiedBar] = useState(false);

  // Kirgach guest promptlar hisobga koʻchiriladi (bir marta, xato boʻlsa joyida qoladi)
  const userId = user?.id ?? null;
  const migratedFor = useRef<string | null>(null);
  useEffect(() => {
    if (!userId || migratedFor.current === userId) return;
    migratedFor.current = userId;
    const prompts = readGuest().prompts;
    if (!prompts.length) return;
    migrateGuestPrompts(prompts)
      .then(() => {
        takeGuestPrompts();
        return refreshUser();
      })
      .catch(() => {
        migratedFor.current = null;
      });
  }, [userId]);

  // Matn tahlili: yozib toʻxtagach tur + 2–3 ta mos vosita (birinchisi tanlanadi)
  const [analyzing, setAnalyzing] = useState(false);
  const analyzeAbort = useRef<AbortController | null>(null);
  const maybeAnalyze = useCallback(async () => {
    const cur = stateRef.current;
    const text = cur.text.trim();
    const idle =
      cur.phase === "idle" || cur.phase === "done" || cur.phase === "error";
    if (text.length < 6 || text === cur.analyzedText || !idle) return;
    analyzeAbort.current?.abort();
    const ctrl = new AbortController();
    analyzeAbort.current = ctrl;
    // 8 s dan uzoq kutilmaydi — mashhur uchlik bilan davom etiladi, backend oʻzi aniqlaydi
    const timer = setTimeout(
      () => ctrl.abort(new DOMException("timeout", "TimeoutError")),
      8000,
    );
    setAnalyzing(true);
    try {
      const a = await analyze({ text, locale }, ctrl.signal);
      const now = stateRef.current;
      const keepUserPick =
        now.aiPicked && now.ai !== null && a.tools.includes(now.ai);
      patch({
        tools: a.tools,
        analyzedText: text,
        suggestedKind: a.kind,
        kindConfidence: a.confidence,
        ai: keepUserPick ? now.ai : (a.tools[0] ?? null),
        aiPicked: keepUserPick,
      });
    } catch {
      const timedOut =
        ctrl.signal.aborted &&
        (ctrl.signal.reason as { name?: string } | undefined)?.name ===
          "TimeoutError";
      // Yangi tahlil boshlangani uchun bekor qilingan boʻlsa — hech narsa qilmaymiz
      if (ctrl.signal.aborted && !timedOut) return;
      // Tahlil boʻlmasa (xato yoki 8 s kechikish) ish davom etadi: mashhur uchlik
      patch({
        tools: ["chatgpt", "claude", "gemini"],
        analyzedText: text,
        ai: null,
        aiPicked: false,
      });
      if (timedOut) setAnalyzing(false);
    } finally {
      clearTimeout(timer);
      if (!ctrl.signal.aborted) setAnalyzing(false);
    }
  }, [locale, patch]);

  // Yozishdan 800 ms keyin (yoki maydondan chiqqanda) tahlil
  const typingTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const onTextChange = (text: string) => {
    patch({ text });
    if (typingTimer.current) clearTimeout(typingTimer.current);
    typingTimer.current = setTimeout(() => void maybeAnalyze(), 800);
  };
  const onTextBlur = () => {
    if (typingTimer.current) clearTimeout(typingTimer.current);
    void maybeAnalyze();
  };
  useEffect(
    () => () => {
      if (typingTimer.current) clearTimeout(typingTimer.current);
    },
    [],
  );

  /** Ish hodisalariga ulanish: birinchi marta ham, yangilanishdan keyin ham shu. */
  const attach = useCallback(
    async (jobId: string) => {
      abortRef.current?.abort();
      const ctrl = new AbortController();
      abortRef.current = ctrl;

      let finalPrompt = "";
      let finalNotes: string[] = [];
      let finished = false;
      patch({
        jobId,
        phase: "loading",
        stage: null,
        prompt: "",
        notes: [],
        score: null,
        criteria: [],
        segments: [],
        parts: [],
        promptId: null,
        saved: false,
        error: null,
      });

      try {
        for await (const ev of jobEvents(jobId, ctrl.signal)) {
          switch (ev.event) {
            case "stage":
              patch({ stage: ev.data.stage });
              break;
            case "classify":
              patch({
                resolvedAi: ev.data.ai,
                ...(stateRef.current.tools.length
                  ? {}
                  : { tools: ev.data.tools }),
                ...(ev.data.ask ? { suggestedKind: ev.data.kind } : {}),
              });
              break;
            case "clarify":
              patch({ questions: ev.data.questions, phase: "clarify" });
              break;
            case "delta":
              finalPrompt += ev.data.text;
              patch({ prompt: finalPrompt, phase: "streaming" });
              break;
            case "reset":
              finalPrompt = "";
              patch({ prompt: "", phase: "loading", stage: "generate" });
              break;
            case "explain":
              finalNotes = ev.data.notes;
              patch({
                notes: finalNotes,
                score: typeof ev.data.score === "number" ? ev.data.score : null,
                criteria: ev.data.criteria ?? [],
                segments: ev.data.segments ?? [],
                parts: ev.data.parts ?? [],
              });
              break;
            case "done":
              finished = true;
              if (ev.data.status === "needs_kind") {
                patch({ phase: "idle", resolvedAi: ev.data.ai });
              } else if (ev.data.status === "needs_clarification") {
                patch({ phase: "clarify", resolvedAi: ev.data.ai });
              } else {
                finalPrompt = ev.data.prompt || finalPrompt;
                const cur = stateRef.current;
                if (currentUser()) {
                  // Server oʻzi saqlaydi; kunlik qoldiq yangilansin
                  void refreshUser();
                } else if (cur.savedJobId !== jobId) {
                  saveGuestPrompt({
                    input_text: cur.text,
                    kind: ev.data.kind,
                    ai: ev.data.ai,
                    clarifications: cur.answers,
                    result: finalPrompt,
                    explanations: finalNotes,
                    locale,
                  });
                }
                patch({
                  prompt: finalPrompt,
                  phase: "done",
                  stage: "done",
                  savedJobId: jobId,
                  resolvedAi: ev.data.ai,
                  promptId: ev.data.prompt_id ?? null,
                  questions: [],
                });
                setPicks({});
              }
              break;
            case "error":
              finished = true;
              patch({ error: ev.data.detail, phase: "error" });
              break;
          }
        }
        if (!finished) {
          // Oqim yakunsiz uzildi (server qayta ishga tushgan boʻlishi mumkin)
          patch({
            phase: finalPrompt ? "done" : "error",
            error: finalPrompt ? null : t("connectionLost"),
          });
        }
      } catch (e) {
        if (ctrl.signal.aborted) return;
        patch({
          error: e instanceof ApiError ? e.message : String(e),
          phase: "error",
        });
      }
    },
    [patch, locale, t],
  );

  const run = useCallback(
    async (
      withAnswers: Record<string, string>,
      forcedKind: Kind | null,
      improve: ImproveBody | null = null,
    ) => {
      const cur = stateRef.current;
      if (cur.text.trim().length < 3) {
        patch({ error: t("textTooShort"), phase: "error" });
        return;
      }
      abortRef.current?.abort();
      patch({
        phase: "loading",
        prompt: "",
        notes: [],
        score: null,
        criteria: [],
        segments: [],
        parts: [],
        promptId: null,
        saved: false,
        error: null,
        jobId: null,
        answers: withAnswers,
      });
      try {
        // Tahlil turga ishonchli boʻlsa (≥ 0.7) — serverda qayta tasniflanmaydi
        const kind =
          forcedKind ??
          (cur.kindConfidence >= 0.7 && cur.analyzedText === cur.text.trim()
            ? cur.suggestedKind
            : null);
        const useRatio = kind !== null && RATIO_KINDS.includes(kind);
        const jobId = await startGenerate({
          text: cur.text,
          ai: cur.ai,
          kind,
          ratio: useRatio ? cur.ratio : null,
          answers: withAnswers,
          locale,
          output_language: "en",
          guest_id: readGuest().id,
          session_id: sessionId(),
          improve,
        });
        await attach(jobId);
      } catch (e) {
        // Limit tugagan (429) — kirgan foydalanuvchida qoldiq serverdan yangilanadi
        if (e instanceof ApiError && e.status === 429 && currentUser()) {
          void refreshUser();
        }
        patch({
          error: e instanceof ApiError ? e.message : String(e),
          phase: "error",
        });
      }
    },
    [attach, patch, locale, t],
  );

  // Sahifa yangilangan / til almashgan: yasalayotgan ishga qayta ulanish
  useEffect(() => {
    const cur = stateRef.current;
    if (cur.jobId && (cur.phase === "loading" || cur.phase === "streaming")) {
      void attach(cur.jobId);
    } else {
      void maybeAnalyze();
    }
    return () => {
      abortRef.current?.abort();
      analyzeAbort.current?.abort();
    };
    // faqat birinchi chizishda
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /**
   * Yagona asosiy harakat. Savollar boʻlsa — belgilangan javoblar bilan,
   * javob berilmaganlari «koʻrsatilmagan» boʻlib ketadi (savol ixtiyoriy).
   */
  const start = () => {
    if (busy || exhausted) return;
    setEditing(false);
    if (s.questions.length) {
      const picked = toAnswers(s.questions, picks);
      const answers = Object.fromEntries(
        s.questions.map((q) => [q.id, picked[q.id] ?? "(not specified)"]),
      );
      track(
        "questions_answered",
        { answered: Object.keys(picked).length, asked: s.questions.length },
        readGuest().id,
      );
      void run(answers, s.kind ?? s.suggestedKind);
      return;
    }
    track(
      "idea_submitted",
      { input: "text", locale, chars: s.text.trim().length, kind: s.kind ?? "auto" },
      readGuest().id,
    );
    patch({ answers: {}, questions: [], resolvedAi: null });
    setPicks({});
    void run({}, s.kind);
  };

  /** «Yaxshilash» va «Tez oʻzgartirish» — savolsiz qayta yozish. */
  const improve = (feedback: string[]) => {
    if (busy || exhausted || !s.prompt) return;
    const fb = feedback.length
      ? feedback
      : s.criteria.filter((c) => !c.ok && c.note).map((c) => c.note);
    void run(s.answers, s.kind ?? s.suggestedKind, {
      previous_prompt: s.prompt,
      feedback: fb,
    });
  };

  /** Boshidan: matn, tanlovlar va natija tozalanadi (guest hisobi saqlanadi). */
  const resetAll = () => {
    abortRef.current?.abort();
    if (s.jobId && busy) void cancelJob(s.jobId);
    setPicks({});
    setEditing(false);
    setS({ ...EMPTY_DRAFT });
  };

  const stop = () => {
    abortRef.current?.abort();
    if (s.jobId) void cancelJob(s.jobId);
    patch({ phase: s.prompt ? "done" : "idle", jobId: null });
  };

  const onSave = (saved: boolean) => {
    if (!s.promptId) return;
    patch({ saved });
    savePrompt(s.promptId, saved).catch(() => patch({ saved: !saved }));
  };

  const copyBar = async () => {
    try {
      await navigator.clipboard.writeText(s.prompt);
      track("prompt_copied", { prompt_id: s.promptId, where: "mobile" }, readGuest().id);
      setCopiedBar(true);
      setTimeout(() => setCopiedBar(false), 1600);
    } catch {
      /* clipboard yoʻq */
    }
  };

  const answeredSomething = Object.values(picks).some(
    (p) => p.chosen.length > 0 || (p.custom && p.text.trim().length > 0),
  );
  const showResult = s.phase === "streaming" || s.phase === "done";
  const resultAi = s.resolvedAi ?? s.ai ?? "chatgpt";
  const hasResult = showResult && s.prompt.length > 0;
  const kindForResult = s.kind ?? s.suggestedKind;
  const collapsedOnMobile = hasResult && !editing;

  return (
    <MotionConfig reducedMotion="user">
      <div className="mx-auto flex w-full max-w-[1280px] flex-1 flex-col px-4 pb-28 pt-5 md:px-8 lg:min-h-0 lg:pb-6 lg:pt-6">
        <div className="grid min-h-0 flex-1 items-start gap-5 lg:grid-cols-[minmax(0,4fr)_minmax(0,6fr)] lg:items-stretch lg:gap-6">
          {/* chap: gʻoya va boshqaruvlar */}
          <div className="flex min-w-0 flex-col lg:min-h-0">
            {/* mobilda natija chiqqach — qisqa xulosa */}
            {collapsedOnMobile && (
              <section
                aria-label={t("ideaSummary")}
                className="flex flex-col gap-3 rounded-[var(--radius-xl)] border border-border bg-surface p-4 lg:hidden"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-body-sm font-bold text-muted">
                    {t("ideaSummary")}
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-9 gap-2 text-accent"
                    onClick={() => setEditing(true)}
                  >
                    <Pencil size={14} />
                    {t("editIdea")}
                  </Button>
                </div>
                <p className="text-body-md text-text">{s.text}</p>
                <div className="flex flex-wrap gap-1.5">
                  {kindForResult && (
                    <Badge>{t(`kinds.${kindForResult}`)}</Badge>
                  )}
                  <Badge>
                    {AI_META[resultAi].name}
                    {AI_META[resultAi].version
                      ? ` ${AI_META[resultAi].version}`
                      : ""}
                  </Badge>
                  {kindForResult && RATIO_KINDS.includes(kindForResult) && (
                    <Badge mono>{s.ratio}</Badge>
                  )}
                </div>
              </section>
            )}

            <div
              className={cn(
                "flex min-h-0 flex-1 flex-col",
                collapsedOnMobile && "hidden lg:flex",
              )}
            >
              <IdeaPanel
                text={s.text}
                onTextChange={onTextChange}
                onTextBlur={onTextBlur}
                onSubmit={start}
                kind={s.kind}
                onKind={(kind) => patch({ kind })}
                suggestedKind={s.suggestedKind}
                tools={s.tools}
                ai={s.ai}
                onAi={(ai) => patch({ ai, aiPicked: true, resolvedAi: null })}
                aiPicked={s.aiPicked}
                analyzing={analyzing}
                ratio={s.ratio}
                onRatio={(ratio: Ratio) => patch({ ratio })}
                clarifying={s.questions.length > 0}
                showDecisions={hasResult || busy}
                busy={busy}
                hasResult={hasResult}
                exhausted={exhausted}
                isUser={Boolean(user)}
                remainingLabel={remainingLabel}
                onStop={stop}
                onReset={resetAll}
              />
            </div>
          </div>

          {/* oʻng: natija */}
          <div className="flex min-w-0 flex-col lg:min-h-0">
            <AnimatePresence mode="wait" initial={false}>
              {s.phase === "error" ? (
                <ErrorResult
                  key="error"
                  message={s.error ?? ""}
                  onRetry={() => void run(s.answers, s.kind)}
                />
              ) : showResult ? (
                <ResultPanel
                  key="result"
                  ai={resultAi}
                  kind={kindForResult}
                  prompt={s.prompt}
                  segments={s.segments}
                  parts={s.parts}
                  notes={s.notes}
                  score={s.score}
                  streaming={s.phase === "streaming"}
                  promptId={s.promptId}
                  saved={s.saved}
                  onSave={onSave}
                  onImprove={
                    s.phase === "done" && !busy && !exhausted
                      ? improve
                      : undefined
                  }
                />
              ) : s.phase === "loading" ? (
                <LoadingResult
                  key="loading"
                  stage={s.stage}
                  ai={s.resolvedAi ?? s.ai}
                />
              ) : s.phase === "clarify" ? (
                <ClarifyCard
                  key="clarify"
                  questions={s.questions}
                  picks={picks}
                  onPicks={setPicks}
                  onSubmit={start}
                  busy={busy}
                />
              ) : (
                <EmptyResult
                  key="empty"
                  onExample={onTextChange}
                />
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>

      {/* mobil: pastdagi yopishqoq panel */}
      <div className="fixed inset-x-0 bottom-0 z-20 flex gap-2.5 border-t border-border bg-bg/92 px-4 pb-7 pt-3 backdrop-blur-xl lg:hidden">
        {hasResult ? (
          <>
            <Button
              variant="secondary"
              aria-label={t("regenerate")}
              className="h-13 w-13 shrink-0 justify-center rounded-[14px] p-0"
              disabled={busy || exhausted}
              onClick={start}
            >
              <RotateCcw size={20} />
            </Button>
            <Button
              variant="primary"
              className="h-13 flex-1 justify-center gap-2.5 rounded-[14px] text-body-md font-bold"
              onClick={() => void copyBar()}
            >
              {copiedBar ? (
                <Check size={18} strokeWidth={2.4} />
              ) : (
                <Copy size={18} />
              )}
              <span aria-live="polite">
                {copiedBar ? tr("copied") : tr("copy")}
              </span>
            </Button>
          </>
        ) : (
          <Button
            variant="primary"
            className="h-13 flex-1 justify-center gap-2.5 rounded-[14px] text-body-md font-bold"
            disabled={busy || exhausted || s.text.trim().length < 3}
            onClick={start}
          >
            <Sparkles size={18} />
            {busy
              ? t("generating")
              : s.questions.length
                ? answeredSomething
                  ? tc("continue")
                  : tc("skip")
                : t("generate")}
          </Button>
        )}
      </div>
    </MotionConfig>
  );
}

function Badge({
  children,
  mono,
}: {
  children: React.ReactNode;
  mono?: boolean;
}) {
  return (
    <span
      className={
        "inline-flex h-6.5 items-center rounded-full border border-border bg-surface-2 px-2.5 text-label-sm font-semibold text-text-2" +
        (mono ? " font-mono" : "")
      }
    >
      {children}
    </span>
  );
}
