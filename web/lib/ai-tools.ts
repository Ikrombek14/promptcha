// AI vositalari va turlar — backend `ai/catalog.py` bilan bir xil qiymatlar.
// Foydalanuvchiga toʻliq roʻyxat koʻrsatilmaydi: tahlil 2–3 ta mos vositani tanlaydi.

export const AI_TOOLS = [
  "chatgpt",
  "claude",
  "gemini",
  "grok",
  "deepseek",
  "perplexity",
  "salomai",
  "midjourney",
  "flux",
  "ideogram",
  "firefly",
  "higgsfield",
  "veo",
  "kling",
  "seedance",
  "runway",
  "pika",
  "heygen",
  "canva",
  "gamma",
  "elevenlabs",
  "cursor",
] as const;
export type AiTool = (typeof AI_TOOLS)[number];

export const KINDS = ["image", "app", "design", "video", "text"] as const;
export type Kind = (typeof KINDS)[number];

export type Family =
  | "chat"
  | "image"
  | "video"
  | "code"
  | "search"
  | "design"
  | "slides"
  | "voice"
  | "avatar";

export type Locale = "uz" | "ru" | "en";

type Meta = {
  name: string;
  version: string; // 2026-09 holati
  dot: string; // brend rangi — faqat 8px nuqta
  family: Partial<Record<Kind, Family>>; // tur → prompt oilasi (yorliq uchun)
};

// Qora brendlar (Grok, Flux, ElevenLabs, Cursor) dark rejimda koʻrinishi uchun matn rangiga bogʻlanadi
export const AI_META: Record<AiTool, Meta> = {
  chatgpt: {
    name: "ChatGPT",
    version: "GPT-6 Astra",
    dot: "#10A37F",
    family: { text: "chat", design: "chat", app: "chat", image: "image" },
  },
  claude: {
    name: "Claude",
    version: "Fable 5.1",
    dot: "#D97706",
    family: { text: "chat", design: "chat", app: "chat" },
  },
  gemini: {
    name: "Gemini",
    version: "3.8 Flash",
    dot: "#4285F4",
    family: { text: "chat", design: "chat", image: "image", video: "video" },
  },
  grok: {
    name: "Grok",
    version: "4.6",
    dot: "var(--text)",
    family: { text: "chat", image: "image", video: "video" },
  },
  deepseek: {
    name: "DeepSeek",
    version: "V4-Pro",
    dot: "#4D6BFE",
    family: { text: "chat", app: "chat" },
  },
  perplexity: {
    name: "Perplexity",
    version: "",
    dot: "#20808D",
    family: { text: "search" },
  },
  salomai: {
    name: "Salom AI",
    version: "",
    dot: "#1D4ED8",
    family: { text: "chat" },
  },
  midjourney: {
    name: "Midjourney",
    version: "v7",
    dot: "#1D4ED8",
    family: { image: "image", design: "image" },
  },
  flux: {
    name: "Flux",
    version: "",
    dot: "var(--text)",
    family: { image: "image", design: "image" },
  },
  ideogram: {
    name: "Ideogram",
    version: "",
    dot: "#7C3AED",
    family: { image: "image", design: "image" },
  },
  firefly: {
    name: "Adobe Firefly",
    version: "",
    dot: "#FF6B00",
    family: { image: "image", design: "image" },
  },
  higgsfield: {
    name: "Higgsfield",
    version: "",
    dot: "#E11D48",
    family: { image: "image", video: "video" },
  },
  veo: {
    name: "Veo",
    version: "3.1",
    dot: "#34A853",
    family: { video: "video" },
  },
  kling: {
    name: "Kling",
    version: "3.0",
    dot: "#0EA5E9",
    family: { video: "video" },
  },
  seedance: {
    name: "Seedance",
    version: "2.0",
    dot: "#EC4899",
    family: { video: "video" },
  },
  runway: {
    name: "Runway",
    version: "Gen-4.5",
    dot: "#059669",
    family: { video: "video" },
  },
  pika: {
    name: "Pika",
    version: "",
    dot: "#F59E0B",
    family: { video: "video" },
  },
  heygen: {
    name: "HeyGen",
    version: "",
    dot: "#6366F1",
    family: { video: "avatar" },
  },
  canva: {
    name: "Canva AI",
    version: "",
    dot: "#00C4CC",
    family: { design: "design", image: "design" },
  },
  gamma: {
    name: "Gamma",
    version: "",
    dot: "#8B5CF6",
    family: { design: "slides", text: "slides" },
  },
  elevenlabs: {
    name: "ElevenLabs",
    version: "",
    dot: "var(--text)",
    family: { text: "voice", video: "voice" },
  },
  cursor: {
    name: "Cursor / Claude Code",
    version: "Agent",
    dot: "var(--text)",
    family: { app: "code" },
  },
};

export function isAiTool(v: unknown): v is AiTool {
  return typeof v === "string" && (AI_TOOLS as readonly string[]).includes(v);
}

/** Vosita + tur → prompt oilasi (yorliq uchun). Mos kelmasa vositaning birinchi oilasi. */
export function familyFor(tool: AiTool, kind: Kind | null): Family {
  const fam = AI_META[tool].family;
  if (kind && fam[kind]) return fam[kind] as Family;
  return Object.values(fam)[0] as Family;
}

export function wordCount(text: string): number {
  return text.trim() ? text.trim().split(/\s+/).length : 0;
}
