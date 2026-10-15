// Mahsulot hodisalari (`POST /api/events`) — voronka oʻlchovi uchun.
// Qoida: hodisa hech qachon foydalanuvchi ishini sekinlashtirmaydi yoki buzmaydi —
// xato yutiladi, javob kutilmaydi.

const SESSION_KEY = "promptcha_session";

/** Brauzer sessiyasi id'si — shaxsiy maʼlumot emas, faqat voronkani bogʻlash uchun. */
export function sessionId(): string {
  if (typeof window === "undefined") return "";
  try {
    let id = sessionStorage.getItem(SESSION_KEY);
    if (!id) {
      id = crypto.randomUUID().slice(0, 32);
      sessionStorage.setItem(SESSION_KEY, id);
    }
    return id;
  } catch {
    return "";
  }
}

export type EventName =
  | "idea_submitted"
  | "questions_answered"
  | "prompt_copied"
  | "prompt_shared"
  | "prompt_feedback"
  | "tool_selected"
  | "voice_started"
  | "voice_transcribed"
  | "voice_failed";

type Payload = Record<string, string | number | boolean | null>;

/** Hodisani yuboradi (javob kutilmaydi). Sahifa yopilsa ham yetib boradi: `keepalive`. */
export function track(name: EventName, payload?: Payload, guestId?: string | null): void {
  if (typeof window === "undefined") return;
  try {
    void fetch("/api/events", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "promptcha",
      },
      body: JSON.stringify({
        session_id: sessionId(),
        events: [{ name, payload: payload ?? null, guest_id: guestId ?? null }],
      }),
      credentials: "include",
      keepalive: true,
    }).catch(() => {});
  } catch {
    /* jim */
  }
}
