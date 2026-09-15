"use client";

import { useEffect, useId, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { AnimatePresence, motion } from "motion/react";
import { LogIn, LogOut, ShieldCheck } from "lucide-react";
import { Link, useRouter } from "@/i18n/navigation";
import { buttonVariants } from "@/components/ui/button";
import { LOGIN_PATH, logout, useUser } from "@/lib/auth";
import { swap } from "@/lib/motion";
import { cn } from "@/lib/utils";

const itemClass =
  "flex w-full items-center gap-2 rounded-[var(--radius-sm)] px-3 py-2 text-left text-body-md text-text transition-colors hover:bg-surface-2 focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-accent";

/**
 * Header'dagi foydalanuvchi holati:
 * yuklanmoqda → skeleton doira; kirmagan → /login havolasi; kirgan → avatar + menyu.
 */
export function UserMenu() {
  const t = useTranslations("auth");
  const user = useUser();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [leaving, setLeaving] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const menuId = useId();

  // Escape va tashqariga bosishda yopiladi
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
        buttonRef.current?.focus();
      }
    };
    const onPointer = (e: PointerEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("pointerdown", onPointer);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("pointerdown", onPointer);
    };
  }, [open]);

  if (user === undefined) {
    return (
      <span
        aria-hidden
        className="block h-9 w-9 animate-pulse rounded-full border border-border bg-surface-2"
      />
    );
  }

  if (user === null) {
    return (
      <Link
        href={LOGIN_PATH}
        aria-label={t("loginShort")}
        className={cn(buttonVariants({ variant: "secondary", size: "sm" }))}
      >
        <LogIn size={16} />
        <span className="hidden sm:inline">{t("loginShort")}</span>
      </Link>
    );
  }

  const label = user.name?.trim() || user.email;
  const initial = label.charAt(0).toUpperCase();

  const onLogout = async () => {
    setLeaving(true);
    try {
      await logout();
    } finally {
      setLeaving(false);
      setOpen(false);
      router.replace("/app");
      router.refresh();
    }
  };

  return (
    <div ref={rootRef} className="relative">
      <button
        ref={buttonRef}
        type="button"
        aria-label={t("menu")}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={menuId}
        onClick={() => setOpen((v) => !v)}
        className={cn(
          "flex h-9 w-9 items-center justify-center overflow-hidden rounded-full border bg-surface-2 text-label-md font-medium text-text transition-colors",
          open ? "border-accent" : "border-border hover:border-muted",
        )}
      >
        {user.avatar_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={user.avatar_url}
            alt=""
            width={36}
            height={36}
            referrerPolicy="no-referrer"
            className="h-full w-full object-cover"
          />
        ) : (
          <span aria-hidden>{initial}</span>
        )}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            key="menu"
            id={menuId}
            role="menu"
            aria-label={t("menu")}
            {...swap}
            className="absolute right-0 top-full z-40 mt-2 w-72 rounded-[var(--radius)] border border-border bg-surface p-2"
          >
            <div className="flex flex-col gap-1 px-3 py-2">
              {user.name && (
                <p className="truncate text-body-md text-text">{user.name}</p>
              )}
              <p className="truncate font-mono text-code-sm text-muted">
                {user.email}
              </p>
              <span
                className={cn(
                  "mt-1 inline-flex w-fit items-center rounded-[var(--radius-sm)] border px-2 py-0.5 text-label-md font-medium",
                  user.plan === "pro"
                    ? "border-accent text-accent"
                    : "border-border text-muted",
                )}
              >
                {user.plan === "pro" ? t("pro") : t("free")}
              </span>
            </div>

            {user.is_admin && (
              <Link
                href="/admin"
                role="menuitem"
                onClick={() => setOpen(false)}
                className={itemClass}
              >
                <ShieldCheck size={16} className="text-muted" />
                {t("admin")}
              </Link>
            )}

            <div aria-hidden className="my-1 h-px bg-border" />

            <button
              type="button"
              role="menuitem"
              disabled={leaving}
              onClick={() => void onLogout()}
              className={cn(itemClass, "disabled:opacity-50")}
            >
              <LogOut size={16} className="text-muted" />
              {t("logout")}
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
