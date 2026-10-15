// Prompt boʻlaklari (`explain` hodisasidagi `segments`/`parts`) — rang va yorliq.
// Toifalar backend `ai/prompts.SEGMENT_TYPES` bilan bir xil boʻlishi shart.

import type { Kind } from "@/lib/ai-tools";

/** Rang uyasi: har kind'da toʻrtta maʼnoviy boʻlak bir xil toʻrt rangga tushadi. */
export type Slot = "object" | "composition" | "light" | "params";

export const SLOT_OF: Record<string, Slot> = {
  // rasm / video
  object: "object",
  composition: "composition",
  light: "light",
  params: "params",
  // matn / dizayn
  role: "object",
  task: "composition",
  requirements: "light",
  format: "params",
  // ilova
  goal: "object",
  stack: "composition",
  features: "light",
  acceptance: "params",
};

/** Boʻlak toifasi boʻyicha CSS klassi (`globals.css` dagi `.sg-*`). */
export function segClass(type: string): string | null {
  const slot = SLOT_OF[type];
  return slot ? `sg sg-${slot}` : null;
}

/** Nuqta/kvadrat rangi (legend va kartalar uchun). */
export function slotColor(type: string): string {
  const slot = SLOT_OF[type] ?? "object";
  return `var(--seg-${slot})`;
}

const LEGEND: Record<string, readonly string[]> = {
  image: ["object", "composition", "light", "params"],
  video: ["object", "composition", "light", "params"],
  text: ["role", "task", "requirements", "format"],
  design: ["role", "task", "requirements", "format"],
  app: ["goal", "stack", "features", "acceptance"],
};

/** Shu kind uchun legend toifalari (rangli izoh qatori). */
export function legendTypes(kind: Kind | null): readonly string[] {
  return LEGEND[kind ?? "text"] ?? LEGEND.text;
}

/** Nisbat faqat shu turlarda maʼnoli (backend `RATIO_KINDS`). */
export const RATIO_KINDS: readonly Kind[] = ["image", "video"];
export const RATIOS = ["1:1", "4:5", "16:9", "9:16"] as const;
export type Ratio = (typeof RATIOS)[number];

/** Nisbat chipidagi kichik ramka oʻlchami (dizayndan). */
export const RATIO_SHAPE: Record<Ratio, { w: number; h: number }> = {
  "1:1": { w: 12, h: 12 },
  "4:5": { w: 11, h: 14 },
  "16:9": { w: 16, h: 9 },
  "9:16": { w: 9, h: 16 },
};

export function isRatio(v: unknown): v is Ratio {
  return typeof v === "string" && (RATIOS as readonly string[]).includes(v);
}
