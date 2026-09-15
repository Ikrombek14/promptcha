import * as React from "react";
import { cn } from "@/lib/utils";

type CalloutProps = React.HTMLAttributes<HTMLDivElement> & {
  tone?: "neutral" | "accent" | "error";
};

export function Callout({ tone = "neutral", className, ...props }: CalloutProps) {
  return (
    <div
      className={cn(
        "rounded-[var(--radius)] border p-3 text-body-md",
        tone === "neutral" && "border-border bg-surface-2",
        tone === "accent" && "border-border border-l-2 border-l-accent bg-surface-2",
        tone === "error" && "border-error bg-error-soft text-text",
        className,
      )}
      {...props}
    />
  );
}

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      aria-hidden
      className={cn("animate-pulse rounded-[var(--radius-sm)] border border-border bg-surface-2", className)}
    />
  );
}

export function Label({ className, ...props }: React.HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn("block text-label-sm font-medium uppercase tracking-wider text-muted", className)}
      {...props}
    />
  );
}
