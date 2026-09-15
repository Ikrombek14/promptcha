"use client";

import { useEffect } from "react";
import { useLocale, useTranslations } from "next-intl";
import { MotionConfig, motion } from "motion/react";
import { useRouter } from "@/i18n/navigation";
import { buttonVariants } from "@/components/ui/button";
import { Callout } from "@/components/ui/callout";
import { googleLoginUrl, useUser } from "@/lib/auth";
import { fadeUp } from "@/lib/motion";
import { cn } from "@/lib/utils";

function GoogleMark({ size = 18 }: { size?: number }) {
  // Google «G» belgisi — bir rangda (brend ranglari ishlatilmaydi)
  return (
    <svg
      viewBox="0 0 24 24"
      width={size}
      height={size}
      aria-hidden
      focusable="false"
    >
      <path
        fill="currentColor"
        d="M21.35 11.1H12v2.9h5.35c-.25 1.4-1.6 4.1-5.35 4.1-3.2 0-5.85-2.65-5.85-5.9S8.8 6.3 12 6.3c1.85 0 3.05.8 3.75 1.45l2.55-2.45C16.7 3.8 14.55 2.8 12 2.8 6.9 2.8 2.8 6.9 2.8 12s4.1 9.2 9.2 9.2c5.3 0 8.85-3.75 8.85-9 0-.6-.05-1.05-.15-1.5z"
      />
    </svg>
  );
}

type Props = {
  /** `?error=google` — Google callback xatosi */
  error?: string | null;
  /** Kirgach qaytish yoʻli (`?next=`), faqat nisbiy */
  next?: string | null;
};

export function LoginCard({ error, next }: Props) {
  const t = useTranslations("auth");
  const locale = useLocale();
  const user = useUser();
  const router = useRouter();

  const target =
    next && next.startsWith("/") && !next.startsWith("//")
      ? next
      : `/${locale}/app`;

  // Kirgan foydalanuvchi bu sahifada turmaydi
  useEffect(() => {
    if (user) router.replace("/app");
  }, [user, router]);

  return (
    <MotionConfig reducedMotion="user">
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate="show"
        className="w-full max-w-[440px] rounded-[var(--radius)] border border-border bg-surface p-6 md:p-8"
      >
        <h1 className="font-serif text-headline-lg text-text">{t("title")}</h1>
        <p className="mt-2 text-body-md text-muted">{t("subtitle")}</p>

        {error === "google" && (
          <Callout tone="error" role="alert" className="mt-5">
            {t("errorGoogle")}
          </Callout>
        )}

        <a
          href={googleLoginUrl(target)}
          className={cn(
            buttonVariants({ variant: "primary", size: "lg" }),
            "mt-6 w-full",
          )}
        >
          <GoogleMark />
          {t("google")}
        </a>

        <p className="mt-4 text-body-sm text-muted">{t("legal")}</p>
      </motion.div>
    </MotionConfig>
  );
}
