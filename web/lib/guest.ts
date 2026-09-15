// Kirmagan foydalanuvchi: 3 ta bepul urinish, natijalar localStorage'da (`promptcha_guest`).

import type { AiTool, Kind } from "@/lib/ai-tools";

export const GUEST_KEY = "promptcha_guest";
export const GUEST_LIMIT = 3;

export type GuestPrompt = {
  id: string;
  input_text: string;
  kind: Kind;
  ai: AiTool;
  clarifications: Record<string, string>;
  result: string;
  explanations: string[];
  locale: string;
  created_at: string;
};

type GuestState = { id: string; prompts: GuestPrompt[] };

const listeners = new Set<() => void>();

/** useSyncExternalStore uchun obuna. */
export function subscribeGuest(cb: () => void): () => void {
  listeners.add(cb);
  return () => listeners.delete(cb);
}

function notify() {
  for (const cb of listeners) cb();
}

function newId(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : Math.random().toString(36).slice(2) + Date.now().toString(36);
}

export function readGuest(): GuestState {
  try {
    const raw = localStorage.getItem(GUEST_KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as Partial<GuestState>;
      if (parsed && typeof parsed.id === "string" && Array.isArray(parsed.prompts)) {
        return { id: parsed.id, prompts: parsed.prompts };
      }
    }
  } catch {
    /* localStorage yoʻq yoki buzilgan */
  }
  // Yangi holat: jimgina yoziladi (notify yoʻq) — readGuest render paytida ham chaqiriladi
  const fresh: GuestState = { id: newId(), prompts: [] };
  try {
    localStorage.setItem(GUEST_KEY, JSON.stringify(fresh));
  } catch {
    /* jim */
  }
  return fresh;
}

export function writeGuest(state: GuestState) {
  try {
    localStorage.setItem(GUEST_KEY, JSON.stringify(state));
  } catch {
    /* yozib boʻlmadi — jim */
  }
  notify();
}

export function guestRemaining(): number {
  return Math.max(0, GUEST_LIMIT - readGuest().prompts.length);
}

export function saveGuestPrompt(p: Omit<GuestPrompt, "id" | "created_at">): GuestPrompt {
  const state = readGuest();
  const item: GuestPrompt = { ...p, id: newId(), created_at: new Date().toISOString() };
  state.prompts.unshift(item);
  writeGuest(state);
  return item;
}
