// Tarix va Kutubxona sahifalari uchun API qatlami.
// Barcha chaqiruvlar kirgan foydalanuvchi uchun (cookie sessiyasi); 401 → login taklifi.

import { apiJson } from "@/lib/api";
import type { AiTool, Kind } from "@/lib/ai-tools";

/** Bazada saqlangan bitta prompt (backend: `Prompt` jadvali). */
export type SavedPrompt = {
  id: string;
  input_text: string;
  /** Yoʻnalish; katalogdan tashqari qiymat kelsa ham buzilmasin */
  kind: Kind | string | null;
  /** AI vositasi kaliti (`lib/ai-tools` dagi AI_META bilan bir xil) */
  ai: AiTool | string | null;
  result: string;
  explanations: string[] | null;
  /** Tekshiruv balli 0–100 (boʻlmasa null) */
  score: number | null;
  is_saved: boolean;
  created_at: string;
};

/** Sahifalangan roʻyxat */
export type Page<T> = {
  items: T[];
  total: number;
  page: number;
  limit: number;
};

function query(page: number, limit: number): string {
  const p = new URLSearchParams({ page: String(page), limit: String(limit) });
  return `?${p.toString()}`;
}

/** Barcha yasalgan promptlar (eng yangisi yuqorida). */
export function listHistory(page = 1, limit = 20): Promise<Page<SavedPrompt>> {
  return apiJson<Page<SavedPrompt>>(
    `/api/prompts/history${query(page, limit)}`,
  );
}

/** Faqat kutubxonaga saqlanganlar. */
export function listLibrary(page = 1, limit = 20): Promise<Page<SavedPrompt>> {
  return apiJson<Page<SavedPrompt>>(
    `/api/prompts/library${query(page, limit)}`,
  );
}

/** Kutubxonaga qoʻshish / olib tashlash → yangilangan element. */
export function setSaved(id: string, saved: boolean): Promise<SavedPrompt> {
  return apiJson<SavedPrompt>(`/api/prompts/${encodeURIComponent(id)}/save`, {
    method: "POST",
    json: { saved },
  });
}

/** Promptni butunlay oʻchirish. */
export function removePrompt(id: string): Promise<{ status: string }> {
  return apiJson<{ status: string }>(`/api/prompts/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
}
