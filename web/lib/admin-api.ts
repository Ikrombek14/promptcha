// Admin panel API: /api/admin/* (faqat admin, cookie sessiya). Hammasi apiJson orqali.
// Kontrakt: docs/superpowers/specs/2026-09-15-auth-admin-design.md → routers/admin.py

import { apiJson } from "@/lib/api";

export type Plan = "free" | "pro";
export type PaymentMethod = "manual" | "payme" | "click";

export type StatsWindow = { today: number; d7: number; d30: number };

export type ToolStat = {
  ai: string;
  generations: number;
  input_tokens: number;
  output_tokens: number;
};

export type ProviderStat = {
  provider: string;
  model: string;
  calls: number;
  input_tokens: number;
  output_tokens: number;
  /** Token soni provayderdan kelmay, taxminan hisoblangan chaqiruvlar */
  estimated_calls: number;
};

export type StageStat = {
  stage: string;
  calls: number;
  input_tokens: number;
  output_tokens: number;
};

export type TopUser = {
  user_id: string;
  email: string;
  generations: number;
  input_tokens: number;
  output_tokens: number;
};

export type DailyStat = {
  /** YYYY-MM-DD */
  date: string;
  generations: number;
  input_tokens: number;
  output_tokens: number;
};

export type AdminStats = {
  days: number;
  active_users: StatsWindow;
  generations: StatsWindow;
  tokens: { input: number; output: number };
  by_tool: ToolStat[];
  by_provider: ProviderStat[];
  by_stage: StageStat[];
  top_users: TopUser[];
  daily: DailyStat[];
};

export type AdminUser = {
  id: string;
  email: string;
  name: string | null;
  avatar_url: string | null;
  plan: Plan;
  pro_until: string | null;
  bonus_generations: number;
  generations_total: number;
  input_tokens: number;
  output_tokens: number;
  created_at: string;
  last_login_at: string | null;
  is_admin: boolean;
};

export type Page<T> = {
  items: T[];
  total: number;
  page: number;
  limit: number;
};

export type GrantBody = {
  plan?: Plan;
  pro_days?: number;
  /** Qoʻshiladi (manfiy ham boʻlishi mumkin) */
  bonus_generations?: number;
};

export type Payment = {
  id: string;
  user_id: string;
  email: string;
  amount: number;
  currency: string;
  method: PaymentMethod;
  days: number;
  note: string | null;
  provider_ref: string | null;
  created_by: string;
  paid_at: string;
};

export type PaymentBody = {
  user_id: string;
  amount: number;
  method: PaymentMethod;
  days: number;
  note?: string;
};

export type LimitKey =
  | "guest_total_generations"
  | "guest_daily_ip_generations"
  | "free_daily_generations";

export type AdminSettings = Record<LimitKey, number> & {
  /** .env dagi standart qiymatlar */
  defaults: Record<LimitKey, number>;
};

export const LIMIT_KEYS: LimitKey[] = [
  "guest_total_generations",
  "guest_daily_ip_generations",
  "free_daily_generations",
];

function qs(params: Record<string, string | number | undefined>): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== "") sp.set(k, String(v));
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

export function getStats(days: number): Promise<AdminStats> {
  return apiJson<AdminStats>(`/api/admin/stats${qs({ days })}`);
}

export function listUsers(
  params: { q?: string; page?: number; limit?: number } = {},
): Promise<Page<AdminUser>> {
  return apiJson<Page<AdminUser>>(`/api/admin/users${qs(params)}`);
}

export function grantUser(id: string, body: GrantBody): Promise<AdminUser> {
  return apiJson<AdminUser>(
    `/api/admin/users/${encodeURIComponent(id)}/grant`,
    { method: "POST", json: body },
  );
}

export function listPayments(
  params: { page?: number; limit?: number } = {},
): Promise<Page<Payment>> {
  return apiJson<Page<Payment>>(`/api/admin/payments${qs(params)}`);
}

export function createPayment(body: PaymentBody): Promise<Payment> {
  return apiJson<Payment>("/api/admin/payments", {
    method: "POST",
    json: body,
  });
}

export function getSettings(): Promise<AdminSettings> {
  return apiJson<AdminSettings>("/api/admin/settings");
}

export function updateSettings(
  body: Partial<Record<LimitKey, number>>,
): Promise<AdminSettings> {
  return apiJson<AdminSettings>("/api/admin/settings", {
    method: "PUT",
    json: body,
  });
}
