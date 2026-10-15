// «Tez oʻzgartirish» chiplari: bitta bosishda promptni qayta yozish (improve oqimi).
// Yorliq foydalanuvchi tilida (`quick.<id>`), modelga ketadigan koʻrsatma — inglizcha.

import type { Kind } from "@/lib/ai-tools";

export type QuickEdit = { id: string; instruction: string };

const IMAGE: QuickEdit[] = [
  { id: "storybook", instruction: "Rewrite in a warm, hand-drawn storybook illustration style." },
  { id: "cinematic", instruction: "Make it cinematic: film lighting, shallow depth of field, dramatic framing." },
  { id: "watercolor", instruction: "Rewrite as a soft watercolour painting with visible paper texture." },
  { id: "warmer", instruction: "Shift the palette to warmer tones: golden, amber, soft reds." },
];

const VIDEO: QuickEdit[] = [
  { id: "dynamic", instruction: "Add a dynamic camera: movement, tracking or orbit shots." },
  { id: "slowmo", instruction: "Make it slow motion with calm, deliberate pacing." },
  { id: "goldenhour", instruction: "Set it at golden hour with warm low sunlight." },
  { id: "closeup", instruction: "Favour close-up shots that show detail and emotion." },
];

const TEXT: QuickEdit[] = [
  { id: "shorter", instruction: "Make the output requirements shorter and tighter; cut every optional part." },
  { id: "simpler", instruction: "Require simpler, everyday language with no jargon." },
  { id: "examples", instruction: "Require concrete examples inside the output." },
  { id: "stricter", instruction: "Make the output format strict: exact sections, order and length." },
];

const APP: QuickEdit[] = [
  { id: "tests", instruction: "Require tests and acceptance criteria for every feature." },
  { id: "simplestack", instruction: "Require the simplest possible stack with the fewest dependencies." },
  { id: "detail", instruction: "Ask for more detail on the data model and the screens." },
  { id: "edge", instruction: "Require edge cases and error states to be handled explicitly." },
];

const DESIGN: QuickEdit[] = [
  { id: "minimal", instruction: "Make it minimal: fewer elements, generous whitespace." },
  { id: "bolder", instruction: "Use bolder, more saturated colours." },
  { id: "contrast", instruction: "Increase contrast and visual hierarchy." },
  { id: "variants", instruction: "Ask for several variants to compare." },
];

const BY_KIND: Record<string, QuickEdit[]> = {
  image: IMAGE,
  video: VIDEO,
  text: TEXT,
  app: APP,
  design: DESIGN,
};

export function quickEdits(kind: Kind | null): QuickEdit[] {
  return BY_KIND[kind ?? "text"] ?? TEXT;
}
