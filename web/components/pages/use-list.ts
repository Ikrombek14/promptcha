"use client";

// Tarix/Kutubxona uchun kichik yuklash hook'i (kutubxonasiz).
// Natija yuklovchi bilan birga saqlanadi — shuning uchun effect ichida setState kerak emas
// (React 19 lint): yuklovchi almashsa `loading` oʻzi true boʻladi.

import { useCallback, useEffect, useMemo, useState } from "react";
import { useLocale } from "next-intl";
import { ApiError } from "@/lib/api";

export type LoadError = {
  message: string;
  /** HTTP kodi (401 → login taklifi), aniq boʻlmasa null */
  status: number | null;
};

export function toLoadError(e: unknown): LoadError {
  if (e instanceof ApiError) return { message: e.message, status: e.status };
  if (e instanceof Error) return { message: e.message, status: null };
  return { message: String(e), status: null };
}

type Result<T> = {
  loader: () => Promise<T>;
  tick: number;
  data?: T;
  error?: LoadError;
};

export function useLoad<T>(loader: () => Promise<T>) {
  const [tick, setTick] = useState(0);
  const [res, setRes] = useState<Result<T> | null>(null);

  useEffect(() => {
    let alive = true;
    loader().then(
      (data) => {
        if (alive) setRes({ loader, tick, data });
      },
      (e: unknown) => {
        if (alive) setRes({ loader, tick, error: toLoadError(e) });
      },
    );
    return () => {
      alive = false;
    };
  }, [loader, tick]);

  const current =
    res && res.loader === loader && res.tick === tick ? res : null;
  const reload = useCallback(() => setTick((t) => t + 1), []);
  /** Yuklangan maʼlumotni joyida yangilash (saqlash/oʻchirishdan keyin) */
  const setData = useCallback((fn: (prev: T) => T) => {
    setRes((prev) =>
      prev && prev.data !== undefined ? { ...prev, data: fn(prev.data) } : prev,
    );
  }, []);

  return {
    loading: current === null,
    data: current?.data,
    error: current?.error,
    reload,
    setData,
  };
}

const INTL_LOCALE: Record<string, string> = {
  uz: "uz-Latn-UZ",
  ru: "ru-RU",
  en: "en-GB",
};

/** Sana-vaqt — foydalanuvchi tilida (karta tepasidagi mono yozuv uchun) */
export function useDateTime(): (iso: string | null | undefined) => string {
  const locale = useLocale();
  return useMemo(() => {
    const fmt = new Intl.DateTimeFormat(INTL_LOCALE[locale] ?? locale, {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
    return (iso) => {
      if (!iso) return "—";
      const d = new Date(iso);
      return Number.isNaN(d.getTime()) ? "—" : fmt.format(d);
    };
  }, [locale]);
}
