"use client";

import { useTranslations } from "next-intl";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

export const MAX_CHARS = 2000;

type Props = {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  onBlur?: () => void;
  /** Boshqaruvlar yashirin paytda maydon kengroq boʻladi */
  tall?: boolean;
  disabled?: boolean;
};

export function Step1Input({ value, onChange, onSubmit, onBlur, tall, disabled }: Props) {
  const t = useTranslations("app");
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-baseline justify-between">
        <label htmlFor="idea" className="text-body-sm text-muted">
          {t("inputLabel")}
        </label>
        <span className="font-mono text-code-sm text-muted">{t("chars", { count: value.length })}</span>
      </div>
      <Textarea
        id="idea"
        rows={4}
        maxLength={MAX_CHARS}
        value={value}
        disabled={disabled}
        placeholder={t("placeholder")}
        onChange={(e) => onChange(e.target.value)}
        onBlur={onBlur}
        onKeyDown={(e) => {
          if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
            e.preventDefault();
            onSubmit();
          }
        }}
        className={cn(
          "transition-[min-height] duration-300 ease-out",
          tall ? "min-h-[220px]" : "min-h-[120px]",
        )}
      />
    </div>
  );
}
