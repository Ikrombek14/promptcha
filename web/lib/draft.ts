// Vosita holati localStorage'da (`promptcha_draft`): sahifa yangilansa yoki til almashsa,
// foydalanuvchi boʻlgan joyidan davom etadi; yasalayotgan ishga (jobId) qayta ulanadi.

import { type AiTool, type Kind, isAiTool } from "@/lib/ai-tools";
import type { ClarifyQuestion, ReviewCriterion } from "@/lib/api";

export const DRAFT_KEY = "promptcha_draft";

export type Phase =
  "idle" | "loading" | "clarify" | "streaming" | "done" | "error";
export type Stage = "classify" | "clarify" | "generate" | "explain" | "done";

export type Draft = {
  v: 2;
  text: string;
  kind: Kind | null;
  /** Tanlangan vosita (tavsiyalardan biri); null → sayt oʻzi tanlaydi */
  ai: AiTool | null;
  /** Ish uchun aniqlangan vosita (classify'dan) */
  resolvedAi: AiTool | null;
  /** Foydalanuvchi vositani oʻzi bosib tanlagan (aks holda tahlil tanlagan) */
  aiPicked: boolean;
  /** Tahlil tavsiya qilgan 2–3 vosita, birinchisi eng mosi */
  tools: AiTool[];
  /** Qaysi matn uchun tahlil qilingan (qayta chaqirmaslik uchun) */
  analyzedText: string | null;
  /** Tahlil turi ishonchi (≥ 0.7 boʻlsa tur avtomatik) */
  kindConfidence: number;
  phase: Phase;
  /** Serverdagi joriy bosqich (stage hodisasi) */
  stage: Stage | null;
  questions: ClarifyQuestion[];
  answers: Record<string, string>;
  suggestedKind: Kind | null;
  prompt: string;
  notes: string[];
  /** Tekshiruv bali 0–100 (explain hodisasi), null — hali yoʻq */
  score: number | null;
  criteria: ReviewCriterion[];
  error: string | null;
  jobId: string | null;
  /** Bu ishning natijasi guest tarixiga yozilgan boʻlsa — qayta yozilmasin (replay) */
  savedJobId: string | null;
};

export const EMPTY_DRAFT: Draft = {
  v: 2,
  text: "",
  kind: null,
  ai: null,
  resolvedAi: null,
  aiPicked: false,
  tools: [],
  analyzedText: null,
  kindConfidence: 0,
  phase: "idle",
  stage: null,
  questions: [],
  answers: {},
  suggestedKind: null,
  prompt: "",
  notes: [],
  score: null,
  criteria: [],
  error: null,
  jobId: null,
  savedJobId: null,
};

/**
 * `?reset=1` bilan ochilsa — qoralama va guest hisobi tozalanadi (sinov uchun).
 * Guest limiti baribir brauzerda; haqiqiy limit keyinroq serverda (usage_log).
 */
export function applyUrlReset(): boolean {
  try {
    const url = new URL(window.location.href);
    if (!url.searchParams.has("reset")) return false;
    localStorage.removeItem(DRAFT_KEY);
    localStorage.removeItem("promptcha_guest");
    url.searchParams.delete("reset");
    // Render paytida chaqiriladi (useState initializer) — URL tozalash keyinga qoldiriladi,
    // aks holda Next router "setState during render" ogohlantirishini beradi.
    setTimeout(() => window.history.replaceState(null, "", url.toString()), 0);
    return true;
  } catch {
    return false;
  }
}

export function loadDraft(): Draft {
  applyUrlReset();
  try {
    const raw = localStorage.getItem(DRAFT_KEY);
    if (!raw) return EMPTY_DRAFT;
    const d = JSON.parse(raw) as Partial<Omit<Draft, "v">> & { v?: number };
    if (!d || (d.v !== 1 && d.v !== 2) || typeof d.text !== "string")
      return EMPTY_DRAFT;
    const draft: Draft = { ...EMPTY_DRAFT, ...d, v: 2 };
    // Eski yoki katalogdan chiqarilgan vositalar (sora, dalle) — tozalanadi
    if (!isAiTool(draft.ai)) draft.ai = null;
    if (!isAiTool(draft.resolvedAi)) draft.resolvedAi = null;
    draft.tools = Array.isArray(draft.tools)
      ? draft.tools.filter(isAiTool)
      : [];
    // Ish boshlanmasdan yangilangan boʻlsa — boshlangʻich holat
    if (
      (draft.phase === "loading" || draft.phase === "streaming") &&
      !draft.jobId
    ) {
      draft.phase = "idle";
    }
    return draft;
  } catch {
    return EMPTY_DRAFT;
  }
}

export function saveDraft(d: Draft) {
  try {
    localStorage.setItem(DRAFT_KEY, JSON.stringify(d));
  } catch {
    /* localStorage yoʻq */
  }
}
