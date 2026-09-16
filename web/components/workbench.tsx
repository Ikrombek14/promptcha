"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  useSyncExternalStore,
} from "react";
import { useLocale, useTranslations } from "next-intl";
import { AnimatePresence, MotionConfig, motion } from "motion/react";
import { LogIn, RotateCcw, Wand2 } from "lucide-react";
import { Link } from "@/i18n/navigation";
import { Button, buttonVariants } from "@/components/ui/button";
import { Callout } from "@/components/ui/callout";
import { StageIndicator } from "@/components/stage-indicator";
import { AI_META } from "@/lib/ai-tools";
import { DUR, EASE_OUT, fadeUp, springPop, swap } from "@/lib/motion";
import type { Variants } from "motion/react";
import { cn } from "@/lib/utils";
import { Step1Input } from "@/components/steps/Step1Input";
import { Step2Type } from "@/components/steps/Step2Type";
import { Step3Ai } from "@/components/steps/Step3Ai";
import { Step4Clarify } from "@/components/steps/Step4Clarify";
import { Step5Result } from "@/components/steps/Step5Result";
import { type Kind, type Locale } from "@/lib/ai-tools";
import {
  ApiError,
  type ImproveBody,
  analyze,
  cancelJob,
  jobEvents,
  startGenerate,
} from "@/lib/api";
import { type Draft, EMPTY_DRAFT, loadDraft, saveDraft } from "@/lib/draft";
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

// Boshqaruvlar guruhi: Yoʻnalish → AI → tugma → hisob, 80 ms qadam bilan; yashirinishi tez
const controlsGroup: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08, delayChildren: 0.05 } },
  exit: { opacity: 0, y: 4, transition: { duration: 0.15 } },
};

export function Workbench() {
  const t = useTranslations("app");
  const tr = useTranslations("result");
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
  // Ish shu sessiyada jonli tugagan boʻlsa — vosita «ochilish» animatsiyasi (reload'da emas)
  const [liveDoneJobId, setLiveDoneJobId] = useState<string | null>(null);

  const busy = s.phase === "loading" || s.phase === "streaming";
  const exhausted = remaining !== null && remaining <= 0;

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
      // Tahlil boʻlmasa (xato yoki 8 s kechikish) ish davom etadi: mashhur uchlik, backend oʻzi aniqlaydi
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

  // Yozish paytida boshqaruvlar yashirin; 800 ms pauza yoki maydondan chiqish — koʻrsatiladi
  const [typing, setTyping] = useState(false);
  const typingTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const settle = () => {
    setTyping(false);
    void maybeAnalyze();
  };
  const onTextChange = (text: string) => {
    patch({ text });
    setTyping(true);
    if (typingTimer.current) clearTimeout(typingTimer.current);
    typingTimer.current = setTimeout(settle, 800);
  };
  const onTextBlur = () => {
    if (typingTimer.current) clearTimeout(typingTimer.current);
    settle();
  };
  useEffect(
    () => () => {
      if (typingTimer.current) clearTimeout(typingTimer.current);
    },
    [],
  );
  const showControls =
    s.phase !== "idle" || (s.text.trim().length >= 6 && !typing);

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
                setLiveDoneJobId(jobId);
                patch({
                  prompt: finalPrompt,
                  phase: "done",
                  stage: "done",
                  savedJobId: jobId,
                  resolvedAi: ev.data.ai,
                });
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
        error: null,
        jobId: null,
      });
      try {
        // Tahlil turga ishonchli boʻlsa (≥ 0.7) — serverda qayta tasniflanmaydi
        const kind =
          forcedKind ??
          (cur.kindConfidence >= 0.7 && cur.analyzedText === cur.text.trim()
            ? cur.suggestedKind
            : null);
        const jobId = await startGenerate({
          text: cur.text,
          ai: cur.ai,
          kind,
          answers: withAnswers,
          locale,
          output_language: "en",
          guest_id: readGuest().id,
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

  const start = () => {
    if (busy || exhausted) return;
    patch({ answers: {}, questions: [], resolvedAi: null });
    void run({}, s.kind);
  };

  const continueWithAnswers = (a: Record<string, string>) => {
    patch({ answers: a });
    void run(a, s.kind ?? s.suggestedKind);
  };

  const skipClarify = () => {
    const a = Object.fromEntries(
      s.questions.map((q) => [q.id, "(not specified)"]),
    );
    patch({ answers: {} });
    void run(a, s.kind ?? s.suggestedKind);
  };

  /** Boshidan: matn, tanlovlar va natija tozalanadi (guest hisobi saqlanadi). */
  const resetAll = () => {
    abortRef.current?.abort();
    if (s.jobId && busy) void cancelJob(s.jobId);
    setLiveDoneJobId(null);
    setS({ ...EMPTY_DRAFT });
  };

  const stop = () => {
    abortRef.current?.abort();
    if (s.jobId) void cancelJob(s.jobId);
    patch({ phase: s.prompt ? "done" : "idle", jobId: null });
  };

  const showResult = s.phase === "streaming" || s.phase === "done";
  const resultAi = s.resolvedAi ?? s.ai ?? "chatgpt";
  const loadingAi = s.resolvedAi ?? s.ai;

  return (
    <MotionConfig reducedMotion="user">
      <div className="min-h-0 flex-1 lg:overflow-hidden">
        <div className="mx-auto grid min-w-0 max-w-[1312px] gap-4 px-4 py-4 md:px-6 lg:h-full lg:grid-cols-2">
          {/* chap: kirish */}
          <section className="flex min-h-0 min-w-0 flex-col gap-4 overflow-y-auto rounded-[var(--radius)] border border-border bg-surface p-4 md:p-5">
            <h1 className="font-serif text-headline-md text-text">
              {t("title")}
            </h1>

            <Step1Input
              value={s.text}
              onChange={onTextChange}
              onBlur={onTextBlur}
              onSubmit={start}
              tall={!showControls}
              disabled={busy}
            />

            <AnimatePresence initial={false}>
              {showControls && (
                <motion.div
                  key="controls"
                  className="flex flex-col gap-4"
                  variants={controlsGroup}
                  initial="hidden"
                  animate="show"
                  exit="exit"
                >
                  <motion.div variants={fadeUp}>
                    <Step2Type
                      value={s.kind}
                      onChange={(kind) => patch({ kind })}
                      suggested={s.suggestedKind}
                      disabled={busy}
                    />
                  </motion.div>
                  <motion.div variants={fadeUp}>
                    <Step3Ai
                      tools={s.tools}
                      kind={s.kind ?? s.suggestedKind}
                      value={s.ai}
                      onChange={(ai) =>
                        patch({ ai, aiPicked: true, resolvedAi: null })
                      }
                      analyzing={analyzing}
                      disabled={busy}
                    />
                  </motion.div>

                  <motion.div variants={fadeUp}>
                    {busy ? (
                      <Button
                        variant="secondary"
                        size="lg"
                        className="w-full justify-between"
                        onClick={stop}
                      >
                        <span className="inline-flex items-center gap-2">
                          <Wand2 size={16} />
                          {t("generating")}
                        </span>
                        <span className="hidden font-mono text-code-sm text-muted sm:inline">
                          {t("stop")}
                        </span>
                      </Button>
                    ) : (
                      <Button
                        variant="primary"
                        size="lg"
                        className="w-full justify-between"
                        disabled={s.phase === "clarify" || exhausted}
                        onClick={start}
                      >
                        <span className="inline-flex items-center gap-2">
                          <Wand2 size={16} />
                          {s.phase === "done" ? t("regenerate") : t("generate")}
                        </span>
                        <span className="hidden font-mono text-code-sm opacity-80 sm:inline">
                          {t("shortcut")}
                        </span>
                      </Button>
                    )}
                  </motion.div>

                  <motion.div variants={fadeUp}>
                    <AnimatePresence mode="wait" initial={false}>
                      {exhausted ? (
                        <motion.div
                          key="exhausted"
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: 6 }}
                          transition={{ duration: DUR.slow, ease: EASE_OUT }}
                        >
                          <Callout
                            tone="error"
                            className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"
                          >
                            <motion.span
                              initial={{ opacity: 0 }}
                              animate={{
                                opacity: 1,
                                transition: { delay: 0.15 },
                              }}
                            >
                              {user ? t("userExhausted") : t("guestExhausted")}
                            </motion.span>
                            {!user && (
                              <motion.span
                                initial={{ opacity: 0, scale: 0.9 }}
                                animate={{
                                  opacity: 1,
                                  scale: 1,
                                  transition: { ...springPop, delay: 0.3 },
                                }}
                                className="shrink-0"
                              >
                                <Link
                                  href="/login"
                                  className={cn(
                                    buttonVariants({
                                      variant: "secondary",
                                      size: "sm",
                                    }),
                                  )}
                                >
                                  <LogIn size={16} />
                                  {t("loginGoogle")}
                                </Link>
                              </motion.span>
                            )}
                          </Callout>
                        </motion.div>
                      ) : (
                        <motion.div
                          key={`left-${remainingLabel ?? "none"}`}
                          {...swap}
                          className="flex min-h-9 items-center justify-between gap-3"
                        >
                          <p
                            className={cn(
                              "font-mono text-code-sm",
                              remaining === 1 ? "text-text" : "text-muted",
                            )}
                          >
                            {remainingLabel}
                          </p>
                          {(s.text || s.phase !== "idle") && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={resetAll}
                            >
                              <RotateCcw size={14} />
                              {t("reset")}
                            </Button>
                          )}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>
                </motion.div>
              )}
            </AnimatePresence>
          </section>

          {/* oʻng: natija */}
          <section className="relative flex min-h-[320px] min-w-0 flex-col overflow-y-auto rounded-[var(--radius)] border border-border bg-surface p-4 md:p-5">
            {showResult && (
              <motion.span
                aria-hidden
                initial={{ scaleY: 0, opacity: 0 }}
                animate={{ scaleY: 1, opacity: 1 }}
                transition={{ duration: 0.4, ease: "easeOut" }}
                className="absolute inset-y-0 left-0 w-0.5 origin-top rounded-l-[var(--radius)] bg-accent"
              />
            )}

            {s.phase === "idle" && (
              <motion.div
                className="flex flex-1 flex-col items-center justify-center text-center"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3 }}
              >
                <p className="font-serif text-headline-sm text-text">
                  {tr("emptyTitle")}
                </p>
                <p className="mt-2 max-w-sm text-body-md text-muted">
                  {tr("emptyBody")}
                </p>
              </motion.div>
            )}

            {s.phase === "loading" && (
              <div
                className="flex flex-1 flex-col items-center justify-center gap-6 text-center"
                aria-busy
              >
                <StageIndicator stage={s.stage} />
                <div className="flex min-h-10 items-center">
                  <AnimatePresence mode="wait" initial={false}>
                    {loadingAi ? (
                      <motion.span
                        key={loadingAi}
                        {...swap}
                        className="inline-flex items-center gap-2 rounded-[var(--radius-sm)] border border-border bg-surface-2 px-3 py-1.5 font-mono text-code-sm text-muted"
                      >
                        <span
                          aria-hidden
                          className="h-2 w-2 rounded-full"
                          style={{ background: AI_META[loadingAi].dot }}
                        />
                        <span className="text-text">
                          {AI_META[loadingAi].name}
                        </span>
                        {AI_META[loadingAi].version && (
                          <span>{AI_META[loadingAi].version}</span>
                        )}
                      </motion.span>
                    ) : (
                      <motion.span
                        key="wait"
                        {...swap}
                        className="font-mono text-code-sm text-muted"
                      >
                        {tr("loading")}
                      </motion.span>
                    )}
                  </AnimatePresence>
                </div>
              </div>
            )}

            {s.phase === "clarify" && (
              <Step4Clarify
                key={s.jobId ?? "clarify"}
                questions={s.questions}
                onSubmit={continueWithAnswers}
                onSkip={skipClarify}
              />
            )}

            {showResult && (
              <Step5Result
                key={`${s.jobId ?? "job"}-${s.phase === "done" ? "done" : "stream"}`}
                ai={resultAi}
                kind={s.kind ?? s.suggestedKind}
                auto={!s.aiPicked}
                prompt={s.prompt}
                notes={s.notes}
                streaming={s.phase === "streaming"}
                stage={s.stage}
                reveal={
                  s.phase === "done" &&
                  liveDoneJobId !== null &&
                  liveDoneJobId === s.jobId
                }
                questions={s.questions}
                answers={s.answers}
                score={s.score}
                criteria={s.criteria}
                onImprove={
                  s.phase === "done" && s.prompt && !busy && !exhausted
                    ? () =>
                        void run(s.answers, s.kind ?? s.suggestedKind, {
                          previous_prompt: s.prompt,
                          feedback: s.criteria
                            .filter((c) => !c.ok && c.note)
                            .map((c) => c.note),
                        })
                    : undefined
                }
              />
            )}

            {s.phase === "error" && (
              <Callout tone="error" className="flex flex-col gap-3">
                <p className="font-medium">{tr("errorTitle")}</p>
                <p>{s.error}</p>
                <div>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => void run(s.answers, s.kind)}
                  >
                    {tr("retry")}
                  </Button>
                </div>
              </Callout>
            )}
          </section>
        </div>
      </div>
    </MotionConfig>
  );
}
