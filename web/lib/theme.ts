// Tema holati: <html data-theme> + localStorage("promptcha_theme"). useSyncExternalStore uchun.

export type Theme = "light" | "dark";
export const THEME_KEY = "promptcha_theme";

const listeners = new Set<() => void>();

export function subscribeTheme(cb: () => void): () => void {
  listeners.add(cb);
  return () => listeners.delete(cb);
}

export function getTheme(): Theme {
  return document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
}

export function getServerTheme(): Theme {
  return "light";
}

export function setTheme(next: Theme) {
  document.documentElement.setAttribute("data-theme", next);
  try {
    localStorage.setItem(THEME_KEY, next);
  } catch {
    /* jim */
  }
  for (const cb of listeners) cb();
}
