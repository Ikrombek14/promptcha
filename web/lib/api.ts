// fetch wrapper + SSE oʻquvchi.
// Backend: POST /api/prompts/generate → {job_id}; GET /api/prompts/jobs/{id} → SSE (replay + jonli)

import type { AiTool, Kind, Locale } from "@/lib/ai-tools";

// SecurityMiddleware talab qiladi: brauzerdagi bizning kodimizdan kelganini bildiradi
const REQUESTED_WITH = { "X-Requested-With": "promptcha" } as const;

export type ClarifyQuestion = {
  id: string;
  question: string;
  options: string[];
};

export type GenerateBody = {
  text: string;
  ai?: AiTool | null; // null → sayt oʻzi tanlaydi
  kind?: Kind | null;
  answers?: Record<string, string>;
  locale: Locale;
  output_language?: Locale;
  guest_id?: string | null;
};

export type SseEvent =
  | {
      event: "stage";
      data: { stage: "classify" | "clarify" | "generate" | "explain" };
    }
  | {
      event: "classify";
      data: {
        kind: Kind;
        confidence: number;
        ask: boolean;
        ai: AiTool;
        tools: AiTool[];
      };
    }
  | { event: "clarify"; data: { questions: ClarifyQuestion[] } }
  | { event: "delta"; data: { text: string } }
  | { event: "reset"; data: Record<string, never> } // provayder uzildi — prompt boshidan
  | { event: "explain"; data: { notes: string[] } }
  | {
      event: "done";
      data: {
        status: "ok" | "needs_kind" | "needs_clarification";
        kind: Kind;
        ai: AiTool;
        prompt: string;
      };
    }
  | { event: "error"; data: { detail: string } };

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function readError(res: Response): Promise<string> {
  try {
    const j = await res.json();
    if (typeof j?.detail === "string") return j.detail;
    // pydantic 422: detail = [{loc, msg, ...}]
    if (Array.isArray(j?.detail)) {
      const msgs = (j.detail as { msg?: string; loc?: unknown[] }[])
        .map((d) =>
          d.loc?.length
            ? `${String(d.loc[d.loc.length - 1])}: ${d.msg ?? ""}`
            : (d.msg ?? ""),
        )
        .filter(Boolean);
      if (msgs.length) return msgs.join("; ");
    }
    if (typeof j?.error === "string") return j.error;
  } catch {
    /* JSON emas */
  }
  return `HTTP ${res.status}`;
}

/** Umumiy JSON soʻrov: xavfsizlik sarlavhasi + cookie; xato → ApiError. 204/boʻsh tana → undefined. */
export async function apiJson<T = unknown>(
  path: string,
  init: RequestInit & { json?: unknown } = {},
): Promise<T> {
  const { json, headers, ...rest } = init;
  const res = await fetch(path, {
    ...rest,
    headers: {
      ...(json !== undefined ? { "Content-Type": "application/json" } : {}),
      ...REQUESTED_WITH,
      ...(headers ?? {}),
    },
    body: json !== undefined ? JSON.stringify(json) : rest.body,
    credentials: "include",
  });
  if (!res.ok) throw new ApiError(await readError(res), res.status);
  if (res.status === 204) return undefined as T;
  const text = await res.text();
  return (text ? JSON.parse(text) : undefined) as T;
}

export type Analysis = { kind: Kind; confidence: number; tools: AiTool[] };

/** Matn tahlili: tur + 2–3 ta eng mos vosita (yozib toʻxtagach chaqiriladi). */
export async function analyze(
  body: { text: string; locale: Locale },
  signal?: AbortSignal,
): Promise<Analysis> {
  const res = await fetch("/api/prompts/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...REQUESTED_WITH },
    body: JSON.stringify(body),
    credentials: "include",
    signal,
  });
  if (!res.ok) throw new ApiError(await readError(res), res.status);
  return (await res.json()) as Analysis;
}

/** Ishni boshlaydi, job id qaytaradi. */
export async function startGenerate(
  body: GenerateBody,
  signal?: AbortSignal,
): Promise<string> {
  const res = await fetch("/api/prompts/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...REQUESTED_WITH },
    body: JSON.stringify(body),
    credentials: "include",
    signal,
  });
  if (!res.ok) throw new ApiError(await readError(res), res.status);
  const j = (await res.json()) as { job_id: string };
  return j.job_id;
}

/** Ishni toʻxtatadi (server tomonda). Xatoni yutadi — UI baribir toʻxtaydi. */
export async function cancelJob(jobId: string): Promise<void> {
  try {
    await fetch(`/api/prompts/jobs/${encodeURIComponent(jobId)}/cancel`, {
      method: "POST",
      headers: REQUESTED_WITH,
      credentials: "include",
    });
  } catch {
    /* jim */
  }
}

/** Ish hodisalari: avval toʻplanganlar (replay), keyin jonli. Qayta ulanish uchun ham shu. */
export function jobEvents(
  jobId: string,
  signal?: AbortSignal,
): AsyncGenerator<SseEvent> {
  return sseStream(`/api/prompts/jobs/${encodeURIComponent(jobId)}`, {
    signal,
  });
}

/** Umumiy SSE oʻquvchi. `signal` bilan bekor qilinadi. */
export async function* sseStream(
  url: string,
  init: RequestInit = {},
): AsyncGenerator<SseEvent> {
  const res = await fetch(url, {
    ...init,
    headers: {
      Accept: "text/event-stream",
      ...REQUESTED_WITH,
      ...(init.headers ?? {}),
    },
    credentials: "include",
  });
  if (!res.ok || !res.body)
    throw new ApiError(await readError(res), res.status);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  const parseBlock = (block: string): SseEvent | null => {
    let event = "message";
    const dataLines: string[] = [];
    for (const line of block.split("\n")) {
      if (line.startsWith("event:")) event = line.slice(6).trim();
      else if (line.startsWith("data:"))
        dataLines.push(line.slice(5).trimStart());
    }
    if (!dataLines.length) return null;
    try {
      return { event, data: JSON.parse(dataLines.join("\n")) } as SseEvent;
    } catch {
      return null;
    }
  };

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    // sse-starlette qatorlarni \r\n bilan ajratadi — CR olib tashlanadi, keyin \n\n boʻyicha boʻlinadi
    buffer += decoder.decode(value, { stream: true }).replace(/\r/g, "");
    let idx: number;
    while ((idx = buffer.indexOf("\n\n")) !== -1) {
      const block = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      const ev = parseBlock(block);
      if (ev) yield ev;
    }
  }
  const tail = buffer.trim();
  if (tail) {
    const ev = parseBlock(tail);
    if (ev) yield ev;
  }
}
