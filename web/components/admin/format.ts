"use client";

import { useMemo } from "react";
import { useLocale } from "next-intl";

const INTL_LOCALE: Record<string, string> = {
  uz: "uz-Latn-UZ",
  ru: "ru-RU",
  en: "en-GB",
};

/** Minglik ajratgichli raqam, sana va sana-vaqt — foydalanuvchi tilida */
export function useFmt() {
  const locale = useLocale();
  return useMemo(() => {
    const tag = INTL_LOCALE[locale] ?? locale;
    const num = new Intl.NumberFormat(tag);
    const date = new Intl.DateTimeFormat(tag, {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
    const dateTime = new Intl.DateTimeFormat(tag, {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
    const short = new Intl.DateTimeFormat(tag, {
      day: "2-digit",
      month: "2-digit",
    });
    const parse = (iso: string | null | undefined): Date | null => {
      if (!iso) return null;
      const d = new Date(iso);
      return Number.isNaN(d.getTime()) ? null : d;
    };
    return {
      n: (v: number | null | undefined) =>
        v === null || v === undefined ? "—" : num.format(v),
      date: (iso: string | null | undefined) => {
        const d = parse(iso);
        return d ? date.format(d) : "—";
      },
      dateTime: (iso: string | null | undefined) => {
        const d = parse(iso);
        return d ? dateTime.format(d) : "—";
      },
      /** "YYYY-MM-DD" → "DD.MM" */
      shortDay: (ymd: string) => {
        const d = parse(`${ymd}T00:00:00`);
        return d ? short.format(d) : ymd;
      },
    };
  }, [locale]);
}

/** Butun manfiy boʻlmagan son; boʻsh yoki notoʻgʻri → null */
export function parseInt0(s: string): number | null {
  if (!/^\d+$/.test(s.trim())) return null;
  const n = Number(s);
  return Number.isSafeInteger(n) ? n : null;
}

/** Butun son (manfiy ham); boʻsh yoki notoʻgʻri → null */
export function parseIntAny(s: string): number | null {
  if (!/^-?\d+$/.test(s.trim())) return null;
  const n = Number(s);
  return Number.isSafeInteger(n) ? n : null;
}
