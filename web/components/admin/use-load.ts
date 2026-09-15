"use client";

// Oddiy async yuklash hook'i (kutubxonasiz). Yuklovchi `useCallback` bilan barqaror boʻlishi kerak —
// natija yuklovchi bilan birga saqlanadi, shuning uchun effect ichida setState kerak emas
// (React 19 lint): yuklovchi almashsa `loading` oʻzi true boʻladi.

import { useCallback, useEffect, useState } from "react";
import { ApiError } from "@/lib/api";

type Result<T> = {
  loader: () => Promise<T>;
  tick: number;
  data?: T;
  error?: string;
};

export function errorMessage(e: unknown): string {
  if (e instanceof ApiError) return e.message;
  if (e instanceof Error) return e.message;
  return String(e);
}

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
        if (alive) setRes({ loader, tick, error: errorMessage(e) });
      },
    );
    return () => {
      alive = false;
    };
  }, [loader, tick]);

  const current =
    res && res.loader === loader && res.tick === tick ? res : null;
  const reload = useCallback(() => setTick((t) => t + 1), []);
  /** Yuklangan maʼlumotni joyida yangilash (masalan, jadval qatori) */
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

/** Qiymatni `ms` dan keyin qaytaradi (qidiruv debounce) */
export function useDebounced<T>(value: T, ms = 400): T {
  const [v, setV] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setV(value), ms);
    return () => clearTimeout(id);
  }, [value, ms]);
  return v;
}
