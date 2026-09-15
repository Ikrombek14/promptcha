// Kirgan foydalanuvchi holati: GET /api/auth/me (cookie bilan), chiqish, useUser() hook.
// `undefined` = hali yuklanmagan, `null` = kirmagan.

import { useSyncExternalStore } from "react";
import { apiJson } from "@/lib/api";
import type { GuestPrompt } from "@/lib/guest";

export type User = {
  id: string;
  email: string;
  name: string | null;
  avatar_url: string | null;
  plan: "free" | "pro";
  pro_until: string | null;
  is_admin: boolean;
  bonus_generations: number;
  /** Bugun qolgan bepul urinishlar (Pro'da null) */
  remaining_today: number | null;
};

type State = User | null | undefined;

let state: State = undefined;
let inflight: Promise<User | null> | null = null;
const listeners = new Set<() => void>();

function notify() {
  for (const cb of listeners) cb();
}

export async function fetchMe(): Promise<User | null> {
  if (inflight) return inflight;
  inflight = apiJson<User>("/api/auth/me")
    .then((u) => u)
    .catch(() => null)
    .then((u) => {
      state = u;
      inflight = null;
      notify();
      return u;
    });
  return inflight;
}

/** Sessiya oʻzgargach (login/logout/koʻchirish) qayta soʻrash. */
export function refreshUser(): Promise<User | null> {
  inflight = null;
  return fetchMe();
}

export async function logout(): Promise<void> {
  try {
    await apiJson("/api/auth/logout", { method: "POST" });
  } finally {
    state = null;
    notify();
  }
}

function subscribe(cb: () => void): () => void {
  listeners.add(cb);
  if (state === undefined && !inflight) void fetchMe();
  return () => listeners.delete(cb);
}

const getSnapshot = () => state;
const getServerSnapshot = (): State => undefined;

/** Joriy foydalanuvchi: undefined (yuklanmoqda) | null (kirmagan) | User. */
export function useUser(): State {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}

/** Hook'siz oʻqish (callback/async ichida): undefined | null | User. */
export function currentUser(): State {
  return state;
}

/**
 * Guest promptlarni kirgan foydalanuvchi hisobiga koʻchirish.
 * Muvaffaqiyatda chaqiruvchi `takeGuestPrompts()` bilan localStorage'ni tozalaydi.
 */
export function migrateGuestPrompts(
  prompts: GuestPrompt[],
): Promise<{ saved: number }> {
  return apiJson<{ saved: number }>("/api/auth/migrate", {
    method: "POST",
    json: {
      prompts: prompts.map((p) => ({
        input_text: p.input_text,
        kind: p.kind,
        ai: p.ai,
        clarifications: p.clarifications,
        result: p.result,
        explanations: p.explanations,
        locale: p.locale,
      })),
    },
  });
}

/** Login sahifasiga yoʻl (locale'siz; Link o'zi qo'shadi). */
export const LOGIN_PATH = "/login";

/** Google'ga yoʻnaltiruvchi API manzili; `next` faqat nisbiy yoʻl. */
export function googleLoginUrl(next: string): string {
  const safe = next.startsWith("/") && !next.startsWith("//") ? next : "/";
  return `/api/auth/google?next=${encodeURIComponent(safe)}`;
}
