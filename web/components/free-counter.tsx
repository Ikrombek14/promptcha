"use client";

import { useSyncExternalStore } from "react";
import { useTranslations } from "next-intl";
import { useUser } from "@/lib/auth";
import { guestRemaining, subscribeGuest } from "@/lib/guest";
import { cn } from "@/lib/utils";

const serverSnapshot = () => null;

/**
 * Headerdagi «Bugun N ta bepul qoldi» — uchta nuqta bilan.
 * Pro foydalanuvchida va qoldiq nomaʼlum boʻlganda koʻrinmaydi.
 */
export function FreeCounter({ className }: { className?: string }) {
  const t = useTranslations("header");
  const user = useUser();
  const guestLeft = useSyncExternalStore<number | null>(
    subscribeGuest,
    guestRemaining,
    serverSnapshot,
  );

  const left = user ? user.remaining_today : user === null ? guestLeft : null;
  if (left === null) return null; // Pro (cheksiz) yoki hali yuklanmagan

  const dots = Math.min(Math.max(left, 0), 3);
  return (
    <span
      className={cn(
        "inline-flex h-9 items-center gap-2 rounded-full border border-border bg-surface-2 px-3",
        "text-label-sm font-semibold text-text-2",
        left <= 1 && "border-[color-mix(in_oklab,var(--seg-light),var(--border)_45%)]",
        className,
      )}
    >
      <span aria-hidden className="flex gap-1">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className={cn(
              "h-1.5 w-1.5 rounded-full",
              i < dots ? "bg-accent" : "bg-border-strong",
            )}
          />
        ))}
      </span>
      <span className="hidden sm:inline">{t("freeLeft", { n: left })}</span>
      <span className="sm:hidden">{t("freeShort", { n: left })}</span>
    </span>
  );
}
